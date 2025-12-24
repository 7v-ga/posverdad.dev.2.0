import os

import psycopg

from tests._db import db_url_for_psycopg, truncate_all, seed_minimal_fks
from scrapy_project.storage_helpers import store_article


def _dsn() -> str:
    return os.getenv("DATABASE_URL") or (
        f"postgresql://{os.getenv('POSTGRES_USER', 'posverdad')}:"
        f"{os.getenv('POSTGRES_PASSWORD', 'posverdad')}@"
        f"{os.getenv('POSTGRES_HOST', 'localhost')}:"
        f"{os.getenv('POSTGRES_PORT', '5432')}/"
        f"{os.getenv('POSTGRES_DB', 'posverdad')}"
    )


def test_store_article_saves_article_and_mentions():
    with psycopg.connect(db_url_for_psycopg()) as conn:
        with conn.cursor() as cur:
            # En este proyecto, DELETE no resetea IDs. Usamos truncate_all (idealmente con RESTART IDENTITY).
            truncate_all(cur)
            seed_minimal_fks(cur)

            article = {
                "title": "Test Article",
                "url": "https://example.com/test",
                "source_id": 1,
                "category_id": 1,
                "publication_date": "2025-01-01T00:00:00Z",
                "scraped_at": "2025-01-01T00:00:00Z",
                "body": "Contenido de prueba.",
                "entities": [{"text": "Test Entity", "label": "ORG"}],
            }

            # store_article retorna el id REAL (PK) generado/actualizado en la tabla
            article_id = store_article(conn, article)

            # Verifica artículo
            cur.execute("SELECT id, title, url FROM articles WHERE id = %s", (article_id,))
            row = cur.fetchone()
            assert row is not None
            assert row[1] == "Test Article"
            assert row[2] == "https://example.com/test"

            # Verifica que guardó entidades (en entity_mentions o normalizadas en articles_entities)
            cur.execute("SELECT COUNT(*) FROM entity_mentions WHERE article_id = %s", (article_id,))
            mentions = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM articles_entities WHERE article_id = %s", (article_id,))
            links = cur.fetchone()[0]

            assert (mentions + links) > 0
