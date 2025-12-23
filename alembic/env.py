# alembic/env.py
from __future__ import annotations

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Asegurar imports del proyecto
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from apps.api.models import Base  # noqa: E402

target_metadata = Base.metadata


def _normalize_db_url(url: str) -> str:
    """
    Fuerza SQLAlchemy a usar psycopg3:
      - postgres://              -> postgresql+psycopg://
      - postgresql://            -> postgresql+psycopg://
      - postgresql+psycopg://   -> postgresql+psycopg://
    """
    url = (url or "").strip()
    if not url:
        return url

    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]

    if url.startswith("postgresql+psycopg://"):
        return url.replace("postgresql+psycopg://", "postgresql+psycopg://", 1)

    # Si no especifica driver, SQLAlchemy tiende a psycopg2; lo forzamos a psycopg3.
    if url.startswith("postgresql://") and not url.startswith("postgresql+"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)

    return url


def get_url() -> str:
    env_url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
    if env_url:
        return _normalize_db_url(env_url)

    ini_url = config.get_main_option("sqlalchemy.url")
    return _normalize_db_url(ini_url)


def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    url = get_url()
    config.set_main_option("sqlalchemy.url", url)

    connectable = engine_from_config(
        config.get_section(config.config_ini_section) or {},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
