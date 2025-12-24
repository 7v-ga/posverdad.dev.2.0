# tests/_db.py
from __future__ import annotations

import os


def db_url_for_psycopg() -> str:
    """
    psycopg.connect() NO acepta URLs estilo SQLAlchemy:
      postgresql+psycopg://...

    Por eso, si viene así desde DATABASE_URL/POSTGRES_URL, lo convertimos a:
      postgresql://...

    Si no existe URL, armamos un DSN estándar desde POSTGRES_*.
    """
    url = (os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL") or "").strip()

    if url.startswith("postgresql+psycopg://"):
        return url.replace("postgresql+psycopg://", "postgresql://", 1)
    if url.startswith("postgresql+psycopg2://"):
        return url.replace("postgresql+psycopg2://", "postgresql://", 1)

    if url.startswith("postgresql://"):
        return url

    return (
        f"postgresql://{os.getenv('POSTGRES_USER', 'posverdad')}:"
        f"{os.getenv('POSTGRES_PASSWORD', 'posverdad')}@"
        f"{os.getenv('POSTGRES_HOST', 'localhost')}:"
        f"{os.getenv('POSTGRES_PORT', '5432')}/"
        f"{os.getenv('POSTGRES_DB', 'posverdad')}"
    )


def truncate_all(cur) -> None:
    """
    Reset robusto para integración:
    - TRUNCATE ... CASCADE para evitar problemas con FKs
    - RESTART IDENTITY para que IDs vuelvan a empezar
    Ajusta la lista si agregas más tablas.
    """
    cur.execute(
        """
        TRUNCATE TABLE
            articles_entities,
            entity_mentions,
            entity_actions,
            articles,
            entities,
            sources,
            categories
        RESTART IDENTITY
        CASCADE
        """
    )


def seed_minimal_fks(cur, *, source_id: int = 1, category_id: int = 1) -> None:
    """
    Crea filas mínimas para FKs.
    Usa ON CONFLICT por si corres más de un test sin truncar por algún motivo.
    """
    cur.execute(
        "INSERT INTO sources (id, name) VALUES (%s, %s) ON CONFLICT (id) DO NOTHING",
        (source_id, "Test Source"),
    )
    cur.execute(
        "INSERT INTO categories (id, name) VALUES (%s, %s) ON CONFLICT (id) DO NOTHING",
        (category_id, "Test Category"),
    )
