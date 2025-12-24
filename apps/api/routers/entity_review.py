from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_

from apps.api.db import get_db
from apps.api import models, schemas

router = APIRouter(prefix="/entity-review", tags=["entity-review"])
DbSession = Annotated[Session, Depends(get_db)]
FiltersDep = Annotated[schemas.MentionListFilters, Depends()]


@router.get("/mentions", response_model=schemas.MentionListResponse, summary="Listar menciones (cola de revisión)")
def list_mentions(
    filters: FiltersDep,
    db: DbSession,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    q = (
        db.query(models.EntityMention)
        .options(joinedload(models.EntityMention.canonical_entity))
    )

    if filters.status:
        q = q.filter(models.EntityMention.status == filters.status)

    if filters.raw_label:
        q = q.filter(models.EntityMention.raw_label == filters.raw_label)

    if filters.q:
        pattern = f"%{filters.q}%"
        q = q.filter(models.EntityMention.raw_text.ilike(pattern))

    # Filtros por artículo (fuente/fecha) vía join con articles
    if any([filters.source_id, filters.date_from, filters.date_to]):
        q = q.join(models.Article, models.Article.id == models.EntityMention.article_id)
        if filters.source_id:
            q = q.filter(models.Article.source_id == filters.source_id)
        if filters.date_from:
            q = q.filter(models.Article.publication_date >= filters.date_from)
        if filters.date_to:
            q = q.filter(models.Article.publication_date <= filters.date_to)

    total = q.count()
    items = (
        q.order_by(models.EntityMention.created_at.desc())
         .offset(offset)
         .limit(limit)
         .all()
    )
    return {"items": items, "total": total}


@router.get("/articles/{article_id}/mentions", response_model=list[schemas.EntityMentionOut], summary="Menciones por artículo")
def mentions_by_article(article_id: int, db: DbSession):
    items = (
        db.query(models.EntityMention)
        .options(joinedload(models.EntityMention.canonical_entity))
        .filter(models.EntityMention.article_id == article_id)
        .order_by(models.EntityMention.id.asc())
        .all()
    )
    return items


@router.patch("/mentions/{mention_id}", response_model=schemas.EntityMentionOut, summary="Actualizar mención (aprobar/rechazar/vincular)")
def update_mention(mention_id: int, payload: schemas.EntityMentionUpdate, db: DbSession):
    m = db.query(models.EntityMention).filter(models.EntityMention.id == mention_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Mention not found")

    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(m, k, v)

    if payload.status in ("APPROVED", "REJECTED"):
        m.reviewed_at = func.now()

    m.updated_at = func.now()
    db.add(m)

    # Si aprobaste con canonical_entity_id, sincroniza articles_entities
    if payload.status == "APPROVED" and payload.canonical_entity_id:
        _upsert_article_entity(db, article_id=m.article_id, entity_id=payload.canonical_entity_id)

    db.commit()
    db.refresh(m)
    return m


@router.post("/simulate", response_model=schemas.ActionSimulateResponse, summary="Simular impacto de una acción")
def simulate_action(req: schemas.ActionSimulateRequest, db: DbSession):
    if req.action_type != "MAP_TO_CANONICAL":
        raise HTTPException(status_code=400, detail="Unsupported action_type")

    q = db.query(models.EntityMention.id, models.EntityMention.article_id).filter(
        func.lower(models.EntityMention.raw_text) == func.lower(req.match_raw_text)
    )
    if req.match_raw_label:
        q = q.filter(models.EntityMention.raw_label == req.match_raw_label)

    if req.scope == "ARTICLE_ONLY":
        # En simulate no sabemos artículo, así que avisamos
        raise HTTPException(status_code=400, detail="Use SELECTION or GLOBAL for simulate, or simulate per article via mentions list")

    rows = q.all()
    mentions_affected = len(rows)
    article_ids = sorted({r.article_id for r in rows})
    return {
        "mentions_affected": mentions_affected,
        "articles_affected": len(article_ids),
        "sample_article_ids": article_ids[:20],
    }


@router.post("/apply", summary="Aplicar acción (global o selección)")
def apply_action(req: schemas.ActionApplyRequest, db: DbSession):
    if req.action_type != "MAP_TO_CANONICAL":
        raise HTTPException(status_code=400, detail="Unsupported action_type")

    if req.scope == "SELECTION":
        if not req.mention_ids:
            raise HTTPException(status_code=400, detail="mention_ids required for SELECTION")
        mentions = (
            db.query(models.EntityMention)
            .filter(models.EntityMention.id.in_(req.mention_ids))
            .all()
        )
    else:
        q = db.query(models.EntityMention).filter(
            func.lower(models.EntityMention.raw_text) == func.lower(req.match_raw_text)
        )
        if req.match_raw_label:
            q = q.filter(models.EntityMention.raw_label == req.match_raw_label)
        mentions = q.all()

    # aplica cambios
    for m in mentions:
        m.canonical_entity_id = req.canonical_entity_id
        m.status = "APPROVED"
        m.decision_scope = "GLOBAL" if req.scope == "GLOBAL" else "ARTICLE_ONLY"
        m.reviewed_at = func.now()
        m.updated_at = func.now()
        db.add(m)
        _upsert_article_entity(db, article_id=m.article_id, entity_id=req.canonical_entity_id)

    # registra auditoría
    action = models.EntityAction(
        action_type=req.action_type,
        scope=req.scope,
        status="APPLIED",
        created_by=req.created_by,
        payload={
            "canonical_entity_id": req.canonical_entity_id,
            "match_raw_text": req.match_raw_text,
            "match_raw_label": req.match_raw_label,
            "mention_ids": req.mention_ids,
            "note": req.note,
        },
    )
    db.add(action)

    db.commit()
    return {"ok": True, "mentions_updated": len(mentions)}


def _upsert_article_entity(db: Session, article_id: int, entity_id: int):
    """
    Upsert simple en articles_entities.
    Si tu modelo ArticleEntity no existe en SQLAlchemy, usa SQL directo.
    """
    db.execute(
        """
        INSERT INTO articles_entities (article_id, entity_id)
        VALUES (:a, :e)
        ON CONFLICT (article_id, entity_id) DO NOTHING
        """,
        {"a": article_id, "e": entity_id},
    )
