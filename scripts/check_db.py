#!/usr/bin/env python3
import os
import sys
import argparse
from typing import Set

import psycopg
from psycopg import OperationalError
from dotenv import load_dotenv

# Cargar variables de entorno desde .env si existe
load_dotenv()

def build_dsn() -> str:
    db = os.getenv("POSTGRES_DB", "posverdad")
    user = os.getenv("POSTGRES_USER", "posverdad")
    pwd = os.getenv("POSTGRES_PASSWORD", "posverdad")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    # psycopg v3 (driver moderno)
    return f"postgresql+psycopg://{user}:{pwd}@{host}:{port}/{db}"

# Ajusta esta lista a tu esquema real
REQUIRED_TABLES: Set[str] = {
    "articles",
    "authors",
    "keywords",
    "entities",
    "articles_authors",
    "articles_keywords",
    "articles_entities",
    "framings",
    "nlp_runs",
    "categories",
    "sources",
}

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Chequea conexión a DB y tablas requeridas.")
    p.add_argument("--ping-only", action="store_true",
                   help="Solo verifica conexión (no chequea tablas).")
    p.add_argument("--dsn", default=None,
                   help="DSN de conexión (si no se pasa, se arma desde POSTGRES_*).")
    return p.parse_args()

def main() -> int:
    args = parse_args()
    dsn = args.dsn or build_dsn()

    try:
        # psycopg3: autocommit por defecto False; para SELECT 1 da igual
        with psycopg.connect(dsn) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
            print("✅ Conexión a la base de datos OK.")

            if args.ping_only:
                return 0

            with conn.cursor() as cur:
                cur.execute("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public';
                """)
                existing = {row[0] for row in cur.fetchall()}

            missing = sorted(REQUIRED_TABLES - existing)
            if missing:
                print(f"⚠️  Faltan tablas críticas: {', '.join(missing)}")
                return 2

            print("✅ Todas las tablas críticas están presentes.")
            return 0

    except OperationalError as e:
        print(f"⏳ DB no disponible todavía: {e}")
        return 1
    except Exception as e:
        print(f"❌ Error verificando DB: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
