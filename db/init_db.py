#!/usr/bin/env python3
"""init_db.py — bootstrap de base de datos (modo Alembic)

Uso típico (con Postgres ya arriba, por ejemplo vía Docker):
  python db/init_db.py --reset
  python db/init_db.py
  python db/init_db.py --reset --seed db/seed_entities_aux.sql

Qué hace:
  1) (opcional) --reset: DROP SCHEMA public CASCADE; CREATE SCHEMA public;
  2) (opcional) aplica db/schema.sql (extensiones/vistas auxiliares)
  3) ejecuta: alembic upgrade head
  4) (opcional) aplica un seed SQL

Variables de entorno (dotenv soportado):
  DATABASE_URL=postgresql+psycopg://user:pass@host:5432/dbname
  (o en su defecto) POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_PORT

Notas:
  - Psycopg (v3) usa DSN estilo: postgresql://... (sin "+psycopg")
  - Alembic/SQLAlchemy sí usa: postgresql+psycopg://...
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse, unquote

import psycopg
from dotenv import load_dotenv


def _load_env() -> None:
    # Carga .env desde raíz del repo si existe
    load_dotenv()


def _get_database_url() -> str | None:
    return os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")


def _psycopg_dsn_from_env() -> str:
    """Construye un DSN compatible con psycopg (postgresql://...)."""
    url = _get_database_url()
    if url:
        # Normaliza driver de SQLAlchemy -> DSN para psycopg
        if url.startswith("postgresql+psycopg://"):
            url = url.replace("postgresql+psycopg://", "postgresql://", 1)
        if url.startswith("postgresql+psycopg2://"):
            url = url.replace("postgresql+psycopg2://", "postgresql://", 1)
        return url

    # fallback por variables sueltas
    db = os.getenv("POSTGRES_DB", "posverdad")
    user = os.getenv("POSTGRES_USER", "posverdad")
    password = os.getenv("POSTGRES_PASSWORD", "posverdad")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    return f"postgresql://{user}:{password}@{host}:{port}/{db}"


def _friendly_conn_info(dsn: str) -> str:
    p = urlparse(dsn)
    user = unquote(p.username or "")
    host = p.hostname or ""
    port = p.port or ""
    db = (p.path or "").lstrip("/")
    return f"user={user} host={host} port={port} db={db}"


def _run_sql(conn: psycopg.Connection, sql: str, label: str) -> None:
    with conn.cursor() as cur:
        cur.execute(sql)
    print(f"✅ {label}")


def _apply_sql_file(conn: psycopg.Connection, path: Path) -> None:
    if not path.exists():
        return
    sql = path.read_text(encoding="utf-8")
    if not sql.strip():
        return
    _run_sql(conn, sql, f"Aplicado {path.as_posix()}")


def _reset_public_schema(conn: psycopg.Connection) -> None:
    print("⚠️  Reset schema public (DROP ... CASCADE)")
    _run_sql(conn, "DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public;", "Schema public recreado")


def _run_alembic_upgrade_head() -> None:
    # Usamos el alembic del venv actual (mismo python que ejecuta este script)
    cmd = [sys.executable, "-m", "alembic", "upgrade", "head"]
    print("▶ Ejecutando:", " ".join(cmd))
    subprocess.run(cmd, check=True)


def main() -> int:
    _load_env()

    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Borra schema public y lo recrea (CASCADE). Úsalo si vas a reconstruir desde 0.")
    parser.add_argument("--no-schema-sql", action="store_true", help="No aplicar db/schema.sql (extensiones/vistas auxiliares).")
    parser.add_argument("--seed", type=str, default="", help="Ruta a un SQL de seed (opcional). Ej: db/seed_entities_aux.sql")
    args = parser.parse_args()

    dsn = _psycopg_dsn_from_env()
    print("Conectando a Postgres:", _friendly_conn_info(dsn))

    try:
        with psycopg.connect(dsn, autocommit=True) as conn:
            if args.reset:
                _reset_public_schema(conn)

            if not args.no_schema_sql:
                # Por convención: db/schema.sql en el repo
                repo_root = Path(__file__).resolve().parents[1]
                schema_path = repo_root / "db" / "schema.sql"
                _apply_sql_file(conn, schema_path)

        # Aplicar migraciones (crea tablas)
        _run_alembic_upgrade_head()

        # Seed opcional (después de migraciones)
        if args.seed:
            seed_path = Path(args.seed).expanduser().resolve()
            with psycopg.connect(dsn, autocommit=True) as conn:
                _apply_sql_file(conn, seed_path)

        print("🎉 DB lista (Alembic head aplicado).")

        return 0
    except subprocess.CalledProcessError as e:
        print("❌ Alembic falló:", e, file=sys.stderr)
        return 2
    except Exception as e:
        print("❌ init_db falló:", e, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
