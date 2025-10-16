#!/usr/bin/env python3
# scripts/retry_bad_dates.py
"""
Detecta URLs con error de fecha en logs y reintenta scraping solo de esas noticias.

- Extrae URLs desde logs (líneas que contienen "⚠️ date malformateada").
- Filtra las que ya estén en la DB (opcional).
- Reintenta con Scrapy en lotes (para no exceder límites de línea de comandos).
"""

from __future__ import annotations

import os
import re
import sys
import argparse
import shutil
import subprocess
from typing import Iterable, List, Set

import psycopg2
from psycopg2 import OperationalError
from dotenv import load_dotenv

load_dotenv()

DB_PARAMS = {
    "dbname": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD") or None,
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
}

DEFAULT_LOG_PATH = "logs/pipeline.log"
DEFAULT_ERR_FILE = "logs/errores_date.txt"
DEFAULT_SPIDER = "el_mostrador"
DEFAULT_BATCH = 50  # URLs por batch para no exceder longitud de CLI


def find_scrapy_binary() -> str:
    """
    Busca 'scrapy' en:
      1) $VIRTUAL_ENV/bin/scrapy
      2) .venv/bin/scrapy
      3) PATH (shutil.which)
    """
    candidates = []
    venv = os.environ.get("VIRTUAL_ENV")
    if venv:
        candidates.append(os.path.join(venv, "bin", "scrapy"))
    candidates.append(os.path.join(".venv", "bin", "scrapy"))
    which = shutil.which("scrapy")
    if which:
        candidates.append(which)

    for c in candidates:
        if c and os.path.isfile(c) and os.access(c, os.X_OK):
            return c
    # último recurso: que el sistema resuelva 'scrapy'
    return "scrapy"


def extract_urls_from_log(log_path: str, err_file: str) -> List[str]:
    urls: Set[str] = set()
    if not os.path.exists(log_path):
        print(f"⚠️  No existe {log_path}. Ejecuta primero el scrape.")
        return []

    url_bracket = re.compile(r"\[(https?://[^\]\s]+)\]")
    url_any = re.compile(r"(https?://\S+)")

    with open(log_path, encoding="utf-8") as f:
        for line in f:
            if "⚠️ date malformateada" in line:
                url = None
                m = url_bracket.search(line) or url_any.search(line)
                if m:
                    url = m.group(1).strip()
                if url:
                    urls.add(url)

    os.makedirs(os.path.dirname(err_file), exist_ok=True)
    with open(err_file, "w", encoding="utf-8") as out:
        for u in sorted(urls):
            out.write(u + "\n")

    print(f"🧾 Extraídas {len(urls)} URL(s) con fecha malformateada. Guardadas en {err_file}")
    return sorted(urls)


def url_in_db(url: str) -> bool:
    """
    Devuelve True si la URL ya existe en articles.url
    """
    try:
        with psycopg2.connect(**DB_PARAMS) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM articles WHERE url = %s LIMIT 1;", (url,))
                return cur.fetchone() is not None
    except OperationalError as e:
        print(f"⏳ DB no disponible al consultar '{url}': {e}")
        return False  # No bloquees el reintento solo por el ping; deja pasar la URL
    except Exception as e:
        print(f"❌ Error consultando DB para '{url}': {e}")
        return False


def chunked(seq: List[str], size: int) -> Iterable[List[str]]:
    for i in range(0, len(seq), size):
        yield seq[i:i + size]


def retry_spider(urls: List[str], spider: str, batch_size: int, dry_run: bool) -> None:
    if not urls:
        print("ℹ️  No hay URLs para reintentar.")
        return

    scrapy_bin = find_scrapy_binary()
    print(f"🕷️  Usando scrapy: {scrapy_bin}")

    total = 0
    for batch in chunked(urls, batch_size):
        urls_str = ",".join(batch)
        cmd = [scrapy_bin, "crawl", spider, "-a", f"custom_urls={urls_str}"]
        total += len(batch)

        if dry_run:
            print(f"🧪 DRY-RUN: {' '.join(cmd)}")
        else:
            print(f"🔁 Reintentando {len(batch)} URL(s)...")
            try:
                subprocess.run(cmd, check=True)
            except subprocess.CalledProcessError as e:
                print(f"❌ Scrapy falló para batch de {len(batch)} URL(s): {e}")
                # Continúa con siguientes batches

    print(f"✅ Reintentos programados/ejecutados para {total} URL(s).")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Reintenta scraping para URLs con fecha malformateada registradas en logs.")
    p.add_argument("--log", default=DEFAULT_LOG_PATH, help=f"Ruta del log a inspeccionar (default: {DEFAULT_LOG_PATH})")
    p.add_argument("--out", default=DEFAULT_ERR_FILE, help=f"Archivo donde guardar las URLs detectadas (default: {DEFAULT_ERR_FILE})")
    p.add_argument("--spider", default=DEFAULT_SPIDER, help=f"Nombre del spider a usar (default: {DEFAULT_SPIDER})")
    p.add_argument("--batch", type=int, default=DEFAULT_BATCH, help=f"Cantidad de URLs por batch (default: {DEFAULT_BATCH})")
    p.add_argument("--skip-db-check", action="store_true", help="No consultar DB; reintenta todas las URLs extraídas del log.")
    p.add_argument("--dry-run", action="store_true", help="No ejecuta scrapy; solo muestra los comandos.")
    return p.parse_args()


def main() -> int:
    args = parse_args()

    urls = extract_urls_from_log(args.log, args.out)
    if not urls:
        return 0

    if args.skip_db_check:
        pending = urls
    else:
        print("🔎 Filtrando URLs que ya están en la DB…")
        pending = [u for u in urls if not url_in_db(u)]
        print(f"➡️  Quedan {len(pending)} URL(s) por reintentar tras consultar DB.")

    retry_spider(pending, args.spider, args.batch, args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
