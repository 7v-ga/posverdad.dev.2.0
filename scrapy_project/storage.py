"""scrapy_project.storage

Capa de compatibilidad.

Históricamente este proyecto tuvo lógica DB en `scrapy_project.storage` (psycopg2).
Desde la migración a Alembic/SQLAlchemy + psycopg3, la implementación vive en
`scrapy_project.storage_helpers`.

Este módulo re-exporta funciones usadas por scripts/tests legacy.
"""

from __future__ import annotations

from .storage_helpers import (
    save_preprocessed_data,
)

__all__ = [
    "save_preprocessed_data",
]