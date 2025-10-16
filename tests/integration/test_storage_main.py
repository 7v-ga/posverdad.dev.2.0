import os
import pytest
import psycopg2
from dotenv import load_dotenv
from scrapy_project.storage_helpers import store_article

load_dotenv()

DB_PARAMS = {
    "dbname": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
}

@pytest.fixture(scope="module")
def db_conn():
    conn = psycopg2.connect(**DB_PARAMS)
    yield conn
    conn.rollback()
    conn.close()

def test_store_article_full(db_conn):
    cur = db_conn.cursor()
    cur.execute("DELETE FROM articles_entities WHERE article_id IN (SELECT id FROM articles WHERE url = %s)", ("https://example.com/full-test",))
    cur.execute("DELETE FROM articles_keywords WHERE article_id IN (SELECT id FROM articles WHERE url = %s)", ("https://example.com/full-test",))
    cur.execute("DELETE FROM articles_authors WHERE article_id IN (SELECT id FROM articles WHERE url = %s)", ("https://example.com/full-test",))
    cur.execute("DELETE FROM framings WHERE article_id IN (SELECT id FROM articles WHERE url = %s)", ("https://example.com/full-test",))
    cur.execute("DELETE FROM articles WHERE url = %s", ("https://example.com/full-test",))
    db_conn.commit()
    cur.close()

    article = {
        "title": "Test completo de artículo",
        "url": "https://example.com/full-test",
        "publication_date": "2025-07-08",
        "body": "Contenido de prueba para análisis completo.",
        "meta_keywords": "prueba, artículo, completo",
        "author": "Juan Test",
        "hash": "hash-test-storage",
        "run_id": "test_run_storage",

        "sentiment": {
            "label": "POS",
            "probs": {"POS": 0.8, "NEU": 0.1, "NEG": 0.1}
        },
        "entities": [
            {"text": "Chile", "label": "LOC"},
            {"text": "Boric", "label": "PER"},
        ],
        "framing": {
            "ideological_frame": "progresista",
            "actors": ["gobierno"],
            "victims": ["pueblo"],
            "antagonists": ["oposición"],
            "emotions": ["esperanza"],
            "summary": "El artículo enmarca el conflicto desde una perspectiva de justicia social."
        }
    }

    cur = db_conn.cursor()
    cur.execute("INSERT INTO nlp_runs (run_id, date) VALUES (%s, CURRENT_DATE) ON CONFLICT DO NOTHING;", ("test_run_storage",))
    db_conn.commit()
    cur.close()

    result = store_article(db_conn, article)
    assert result is not None
