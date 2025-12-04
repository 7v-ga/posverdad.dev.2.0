# apps/api/schemas.py

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


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
