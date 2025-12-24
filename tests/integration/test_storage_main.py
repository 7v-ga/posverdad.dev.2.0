# tests/integration/test_storage_main.py
import os

import psycopg

from tests._db import db_url_for_psycopg
from scrapy_project.storage_helpers import store_article


def _db_url_for_psycopg() -> str:
    """
    psycopg (driver) acepta:
      - URI: postgresql://user:pass@host:port/dbname
      - conninfo: host=... dbname=... user=... password=...

    SQLAlchemy usa URIs con driver:
      - postgresql+psycopg://...
      - postgresql+psycopg2://...

    Acá normalizamos DATABASE_URL para psycopg.
    """
    url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
    if url:
        url = url.strip()
        if url.startswith("postgresql+psycopg://"):
            return url.replace("postgresql+psycopg://", "postgresql://", 1)
        if url.startswith("postgresql+psycopg2://"):
            return url.replace("postgresql+psycopg2://", "postgresql://", 1)
        return url

    user = os.getenv("POSTGRES_USER", "posverdad")
    password = os.getenv("POSTGRES_PASSWORD", "posverdad")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "posverdad")
    return f"postgresql://{user}:{password}@{host}:{port}/{db}"


def _reset_db(cur) -> None:
    # Orden: tablas puente / dependientes primero
    cur.execute("DELETE FROM articles_entities")
    cur.execute("DELETE FROM entity_mentions")
    cur.execute("DELETE FROM entity_actions")
    cur.execute("DELETE FROM articles")
    cur.execute("DELETE FROM entities")
    cur.execute("DELETE FROM sources")
    cur.execute("DELETE FROM categories")


def test_store_article_inserts_article_and_relations():
    with psycopg.connect(db_url_for_psycopg()) as conn:
        with conn.cursor() as cur:
            _reset_db(cur)

            cur.execute("INSERT INTO sources (id, name) VALUES (%s, %s)", (1, "Fuente Test"))
            cur.execute("INSERT INTO categories (id, name) VALUES (%s, %s)", (1, "Categoría Test"))

            article = {
                # OJO: store_article NO usa este id como PK; lo dejamos pero el test no debe asumirlo.
                "id": 1,
                "title": "Título de Prueba",
                "url": "http://example.com/test",
                "source_id": 1,
                "category_id": 1,
                "publication_date": "2025-01-01T00:00:00Z",
                "scraped_at": "2025-01-01T00:00:00Z",
                "body": "Texto de prueba. " * 10,
                "entities": [
                    {"text": "Estado", "label": "LOC"},
                    {"text": "IPS", "label": "ORG"},
                ],
                "preprocessed_data": {"entities": [{"text": "Estado", "label": "LOC"}]},
            }

            # store_article retorna el id REAL de la fila en articles
            article_id = store_article(conn, article)

            # Cursor NUEVO después del commit
            with conn.cursor() as cur2:
                cur2.execute(
                    "SELECT title, len_chars, url FROM articles WHERE id = %s",
                    (article_id,),
                )
                row = cur2.fetchone()

            assert row is not None
            assert row[0] == "Título de Prueba"
            assert row[1] is not None
            assert row[2] == "http://example.com/test"

            # Validación alternativa por url (por si quieres doble certeza)
            cur.execute("SELECT id FROM articles WHERE url = %s", ("http://example.com/test",))
            row2 = cur.fetchone()
            assert row2 is not None
            assert int(row2[0]) == int(article_id)

            # Entities pueden persistirse como menciones crudas y/o normalizadas.
            cur.execute("SELECT COUNT(*) FROM entity_mentions WHERE article_id = %s", (article_id,))
            mentions = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM articles_entities WHERE article_id = %s", (article_id,))
            links = cur.fetchone()[0]
            assert (mentions + links) > 0

        conn.commit()
