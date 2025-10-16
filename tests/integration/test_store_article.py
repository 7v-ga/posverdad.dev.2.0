# tests/integration/test_store_article.py
# Test de integración de almacenamiento de artículo (transacción por item)

import os
import pytest
import psycopg2
from datetime import date
from dotenv import load_dotenv
from scrapy_project.storage_helpers import store_article

pytestmark = pytest.mark.integration
load_dotenv()

DB_PARAMS = {
    "dbname": os.getenv("POSTGRES_DB", "posverdad"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "postgres"),
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
}

TEST_URL = "https://example.com/integration-test"
TEST_RUN = "run-test-unitario"

@pytest.fixture(scope="module")
def db_conn():
    conn = psycopg2.connect(**DB_PARAMS)
    yield conn
    conn.close()

def test_store_article_full(db_conn):
    with db_conn:
        with db_conn.cursor() as cur:
            # Limpieza por URL (defensiva)
            cur.execute("DELETE FROM framings WHERE article_id IN (SELECT id FROM articles WHERE url = %s)", (TEST_URL,))
            cur.execute("DELETE FROM articles_entities WHERE article_id IN (SELECT id FROM articles WHERE url = %s)", (TEST_URL,))
            cur.execute("DELETE FROM articles_keywords WHERE article_id IN (SELECT id FROM articles WHERE url = %s)", (TEST_URL,))
            cur.execute("DELETE FROM articles_authors  WHERE article_id IN (SELECT id FROM articles WHERE url = %s)", (TEST_URL,))
            cur.execute("DELETE FROM articles WHERE url = %s", (TEST_URL,))

            # Prerrequisitos mínimos
            cur.execute("INSERT INTO categories (id, name) VALUES (1, 'prueba') ON CONFLICT (id) DO NOTHING;")
            cur.execute("INSERT INTO sources (id, name, domain) VALUES (1, 'Fuente Test', 'example.com') ON CONFLICT (id) DO NOTHING;")
            cur.execute("INSERT INTO nlp_runs (run_id, date) VALUES (%s, CURRENT_TIMESTAMP) ON CONFLICT (run_id) DO NOTHING;", (TEST_RUN,))

            article = {
                "title": "Artículo integración",
                "url": TEST_URL,
                "publication_date": date.today(),
                "body": "Texto extenso de ejemplo para test completo.",
                "meta_keywords": "test, integración",
                "author": "Ana Test",
                "run_id": TEST_RUN,
                "category_id": 1,
                "source_id": 1,          # store_article no lo usa hoy, pero no molesta
                "image": None,
                "meta_description": "Meta test",
                # ⚠️ hash eliminado — body_hash lo deriva store_article automáticamente
                "polarity": 0.5,
                "subjectivity": 0.6,
                "language": "es",
                "sentiment": {"label": "POS", "probs": {"POS": 0.7, "NEU": 0.2, "NEG": 0.1}},
                "entities": [
                    {"text": "Chile", "label": "LOC"},
                    {"text": "Prueba", "label": "ORG"},
                ],
                "framing": {
                    "ideological_frame": "neutral",
                    "actors": ["estado"],
                    "victims": ["sociedad"],
                    "antagonists": ["corrupción"],
                    "emotions": ["indignación"],
                    "summary": "El texto explora la tensión entre sociedad y poder.",
                },
            }

            # 👉 Pasamos CURSOR (nuevo flujo): commit lo hace el 'with db_conn:'
            article_id = store_article(cur, article)
            assert isinstance(article_id, int) and article_id > 0

            # body_hash debe haberse seteado
            cur.execute("SELECT body_hash FROM articles WHERE id = %s", (article_id,))
            bh = cur.fetchone()[0]
            assert bh is not None and len(bh) == 64

            # Verificaciones básicas de relaciones
            cur.execute("SELECT COUNT(*) FROM articles_authors WHERE article_id = %s", (article_id,))
            assert cur.fetchone()[0] >= 1

            cur.execute("SELECT COUNT(*) FROM articles_keywords WHERE article_id = %s", (article_id,))
            assert cur.fetchone()[0] >= 2

            cur.execute("SELECT COUNT(*) FROM articles_entities WHERE article_id = %s", (article_id,))
            assert cur.fetchone()[0] >= 2

            cur.execute("SELECT COUNT(*) FROM framings WHERE article_id = %s", (article_id,))
            assert cur.fetchone()[0] == 1
