# apps/api/schemas.py

from datetime import date, datetime
from typing import Optional, Any, Literal

from pydantic import BaseModel, ConfigDict, Field


MentionStatus = Literal["PENDING", "APPROVED", "REJECTED"]
DecisionScope = Literal["UNDECIDED", "GLOBAL", "ARTICLE_ONLY"]
ApplyScope = Literal["GLOBAL", "ARTICLE_ONLY", "SELECTION"]


# ==========================
# Source (catálogo simple)
# ==========================


class SourceOut(BaseModel):
    id: int
    name: str
    domain: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ==========================
# Articles (summary + detail)
# ==========================


class ArticleSummary(BaseModel):
    """
    Esquema para listar artículos en tabla (listado /cards).
    """
    id: int
    title: str
    url: str
    domain: Optional[str] = None

    publication_date: Optional[date] = None
    published_at: Optional[datetime] = None
    scraped_at: Optional[datetime] = None

    polarity: Optional[float] = None
    subjectivity: Optional[float] = None
    language: Optional[str] = None

    # 🔢 Longitud del cuerpo (calculada en backend a partir de Article.body)
    len_chars: Optional[int] = Field(
        default=None,
        description="Longitud en caracteres del cuerpo del artículo.",
    )

    # 🧠 Datos preprocesados (JSON crudo: entidades, framing, etc.)
    preprocessed_data: dict[str, Any] | None = Field(
        default=None,
        description="Datos preprocesados del artículo (por ejemplo, entidades crudas).",
    )

    source: Optional[SourceOut] = Field(
        default=None,
        description="Fuente asociada (name/domain). Puede ser null si solo hay dominio.",
    )

    model_config = ConfigDict(from_attributes=True)


class ArticleDetail(ArticleSummary):
    """
    Esquema para vista de detalle de artículo.
    Hereda todos los campos de Summary y añade contenido completo.
    """
    subtitle: Optional[str] = None
    body: str
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = None
    image: Optional[str] = None
    run_id: Optional[str] = None


# ==========================
# Filtros de búsqueda
# ==========================


class ArticleFilters(BaseModel):
    """
    Se usa con Depends() en el endpoint como filtros server-side.
    """
    q: Optional[str] = Field(
        default=None,
        description="Búsqueda simple en título/cuerpo (ILIKE).",
    )
    source_id: Optional[int] = Field(default=None)
    entity_id: Optional[int] = Field(
        default=None,
        description="Filtro por entidad (pendiente de join con articles_entities).",
    )
    date_from: Optional[date] = Field(default=None)
    date_to: Optional[date] = Field(default=None)

    model_config = ConfigDict(extra="forbid")

class EntityOut(BaseModel):
    id: int
    name: str
    type: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class EntityMentionOut(BaseModel):
    id: int
    article_id: int
    raw_text: str
    raw_label: Optional[str] = None
    canonical_entity_id: Optional[int] = None
    canonical_entity: Optional[EntityOut] = None
    status: MentionStatus
    decision_scope: DecisionScope
    note: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class EntityMentionUpdate(BaseModel):
    status: Optional[MentionStatus] = None
    decision_scope: Optional[DecisionScope] = None
    canonical_entity_id: Optional[int] = None
    note: Optional[str] = None
    reviewed_by: Optional[str] = None

class MentionListResponse(BaseModel):
    items: list[EntityMentionOut]
    total: int

class MentionListFilters(BaseModel):
    q: Optional[str] = None
    status: Optional[MentionStatus] = "PENDING"
    raw_label: Optional[str] = None
    source_id: Optional[int] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    model_config = ConfigDict(extra="forbid")

class ActionSimulateRequest(BaseModel):
    action_type: Literal["MAP_TO_CANONICAL"]
    scope: ApplyScope
    canonical_entity_id: int
    match_raw_text: str
    match_raw_label: Optional[str] = None

class ActionSimulateResponse(BaseModel):
    mentions_affected: int
    articles_affected: int
    sample_article_ids: list[int]

class ActionApplyRequest(ActionSimulateRequest):
    # Para SELECTION: ids explícitos
    mention_ids: Optional[list[int]] = None
    created_by: Optional[str] = None
    note: Optional[str] = None
