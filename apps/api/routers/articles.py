# apps/api/routers/articles.py

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from apps.api.db import get_db
from apps.api import models, schemas

router = APIRouter(
    prefix="/articles",
    tags=["articles"],
)

DbSession = Annotated[Session, Depends(get_db)]
ArticleFiltersDep = Annotated[schemas.ArticleFilters, Depends()]


@router.get(
    "/",
    response_model=list[schemas.ArticleSummary],
    summary="Listar artículos",
)
def list_articles(
    filters: ArticleFiltersDep,
    db: DbSession,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """
    Listado paginado de artículos con filtros básicos.
    Incluye:
      - source (join simple)
      - entities normalizadas (N:M)
      - preprocessed_data (JSONB crudo)
    """
    query = (
        db.query(models.Article)
        .options(
            joinedload(models.Article.source),
            joinedload(models.Article.entities),
        )
    )

    # Filtro de búsqueda simple en título/cuerpo
    if filters.q:
        pattern = f"%{filters.q}%"
        query = query.filter(
            or_(
                models.Article.title.ilike(pattern),
                models.Article.body.ilike(pattern),
            )
        )

    # Filtro por fuente
    if filters.source_id:
        query = query.filter(models.Article.source_id == filters.source_id)

    # Filtros de fecha
    if filters.date_from:
        query = query.filter(models.Article.publication_date >= filters.date_from)
    if filters.date_to:
        query = query.filter(models.Article.publication_date <= filters.date_to)

    # Filtro por entidad (normalizada)
    if filters.entity_id:
        query = query.join(
            models.Article.entities
        ).filter(models.Entity.id == filters.entity_id)

    query = (
        query.order_by(models.Article.scraped_at.desc().nullslast())
        .offset(offset)
        .limit(limit)
    )

    articles = query.all()
    return articles


@router.get(
    "/{article_id}",
    response_model=schemas.ArticleDetail,
    summary="Obtener detalle de un artículo",
)
def get_article(
    article_id: int,
    db: DbSession,
):
    """
    Detalle de un artículo por ID.
    Incluye:
      - source
      - entities normalizadas
      - preprocessed_data
    """
    article = (
        db.query(models.Article)
        .options(
            joinedload(models.Article.source),
            joinedload(models.Article.entities),
        )
        .filter(models.Article.id == article_id)
        .first()
    )

    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")

    return article
