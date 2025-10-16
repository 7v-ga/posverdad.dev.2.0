#!/usr/bin/env python3
"""
Espera activa a que Postgres acepte conexiones.

Uso:
  python scripts/wait_db.py
  python scripts/wait_db.py --timeout 60 --interval 2 --ping-only
"""

import os
import sys
import time
import argparse

import psycopg
from psycopg import OperationalError
from dotenv import load_dotenv

load_dotenv()

def build_dsn() -> str:
    db = os.getenv("POSTGRES_DB", "postverdad")
    user = os.getenv("POSTGRES_USER", "postverdad")
    pwd = os.getenv("POSTGRES_PASSWORD", "postverdad")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    return f"postgresql+psycopg://{user}:{pwd}@{host}:{port}/{db}"

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Waiter para Postgres.")
    p.add_argument("--timeout", type=int, default=60,
                   help="Tiempo máximo en segundos (default: 60).")
    p.add_argument("--interval", type=float, default=1.5,
                   help="Intervalo entre reintentos (segundos, default: 1.5).")
    p.add_argument("--dsn", default=None,
                   help="DSN de conexión (si no se pasa, se arma desde POSTGRES_*).")
    p.add_argument("--ping-only", action="store_true",
                   help="Solo SELECT 1 (no valida tablas).")
    return p.parse_args()

def check_once(dsn: str, ping_only: bool) -> bool:
    try:
        with psycopg.connect(dsn) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
        return True
    except OperationalError:
        return False
    except Exception:
        # Para waiter, cualquier excepción se considera "no listo"
        return False

def main() -> int:
    args = parse_args()
    dsn = args.dsn or build_dsn()

    deadline = time.time() + args.timeout
    attempt = 0

    while time.time() < deadline:
        attempt += 1
        if check_once(dsn, args.ping_only):
            print(f"✅ Postgres listo (attempt {attempt})")
            return 0
        print(f"⏳ Esperando DB (attempt {attempt})...")
        time.sleep(args.interval)

    print("❌ Tiempo de espera agotado: Postgres no respondió a tiempo")
    return 1

if __name__ == "__main__":
    sys.exit(main())
