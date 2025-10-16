#!/usr/bin/env python3
# init_db.py — reset y creación de esquema para Posverdad
# Soporta:
#   --reset           : Borra todo antes de crear (con confirmación)
#   --no-confirm      : Omite confirmación (o usa env FORCE_RESET=1)
#   --drop-tables     : En vez de DROP SCHEMA, dropea tablas en orden
#   --seed            : Ejecuta seed_entities_aux.sql si existe
#
# Variables de entorno (dotenv soportado):
#   POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_PORT
#   FORCE_RESET=1   -> omite confirmación
#
import os
import sys
import psycopg2
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

DB_PARAMS = {
    "dbname": os.getenv("POSTGRES_DB", "posverdad"),
    "user": os.getenv("POSTGRES_USER", "posverdad"),
    "password": os.getenv("POSTGRES_PASSWORD", "posverdad"),
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
}

HERE = Path(__file__).resolve().parent
SCHEMA_FILE = HERE / "schema.sql"
SEED_FILE = HERE / "seed_entities_aux.sql"

def connect():
    conn = psycopg2.connect(**DB_PARAMS)
    conn.autocommit = True
    return conn

def exec_sql(conn, sql_text: str, label: str = "SQL"):
    with conn.cursor() as cur:
        cur.execute(sql_text)
    print(f"✅ Ejecutado: {label}")

def exec_sql_file(conn, path: Path):
    if not path.exists():
        raise FileNotFoundError(f"No se encontró el archivo SQL: {path}")
    sql = path.read_text(encoding="utf-8")
    exec_sql(conn, sql, label=str(path.name))

def drop_schema(conn):
    # Borra TODO el esquema público y lo recrea
    print("⚠️  DROP SCHEMA public CASCADE …")
    exec_sql(conn, "DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public;")
    print("✅ Esquema 'public' recreado.")

def drop_tables(conn):
    # Alternativa granular (por si no quieres DROP SCHEMA)
    # Orden cuidadoso por FKs
    tables = [
        # Auxiliares primero
        "entity_aliases",
        "entity_blocklist",
        # Relaciones N:M y dependientes
        "framings",
        "articles_categories",
        "articles_entities",
        "articles_keywords",
        "articles_authors",
        # Base
        "articles",
        "entities",
        "keywords",
        "categories",
        "authors",
        "sources",
        "nlp_runs",
    ]
    with conn.cursor() as cur:
        for t in tables:
            cur.execute(f'DROP TABLE IF EXISTS {t} CASCADE;')
            print(f"• DROP TABLE {t} (si existía)")
    print("✅ Todas las tablas objetivo fueron dropeadas (si existían).")

def ask_confirm():
    ans = input("¿Estás seguro/a de eliminar la base (s/N)? ").strip().lower()
    return ans == "s"

def main():
    reset = "--reset" in sys.argv
    no_confirm = ("--no-confirm" in sys.argv) or (os.getenv("FORCE_RESET") == "1")
    use_drop_tables = "--drop-tables" in sys.argv
    do_seed = "--seed" in sys.argv

    print("Conectando a PostgreSQL con:", DB_PARAMS)
    try:
        conn = connect()

        if reset:
            if not no_confirm:
                if not ask_confirm():
                    print("❌ Acción cancelada.")
                    return
            if use_drop_tables:
                drop_tables(conn)
            else:
                drop_schema(conn)

        # Crear esquema
        print(f"📄 Aplicando {SCHEMA_FILE.name} …")
        exec_sql_file(conn, SCHEMA_FILE)

        # Seed opcional
        if do_seed and SEED_FILE.exists():
            print(f"🌱 Aplicando seed {SEED_FILE.name} …")
            exec_sql_file(conn, SEED_FILE)
        elif do_seed:
            print(f"⚠️  Pediste --seed pero no existe {SEED_FILE.name}. Saltando.")

        print("🎉 Base de datos lista.")
        conn.close()
    except Exception as e:
        print("❌ Error en init_db:", e)
        sys.exit(1)

if __name__ == "__main__":
    main()
