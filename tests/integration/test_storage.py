# tests/integration/test_storage.py

import os
import pytest
import psycopg2
from dotenv import load_dotenv

from scrapy_project.storage_helpers import (
    save_authors,
    save_keywords,
    save_entities,
    save_framing,
)

pytestmark = pytest.mark.integration

load_dotenv()

DB_PARAMS = {
    "dbname": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
}

TEST_URL = "https://example.com/test"
TEST_RUN = "test_run"


@pytest.fixture(scope="module")
def db_conn():
    conn = psycopg2.connect(**DB_PARAMS)
    yield conn
    conn.close()


@pytest.fixture
def test_article_id(db_conn):
    """
    Crea un artículo mínimo y devuelve su id.
    Limpia relaciones previas del mismo URL para evitar residuos.
    Usa transacciones con context managers (commit al salir).
    """
    with db_conn:
        with db_conn.cursor() as cur:
            # Limpieza defensiva por URL
            cur.execute("DELETE FROM framings WHERE article_id IN (SELECT id FROM articles WHERE url = %s)", (TEST_URL,))
            cur.execute("DELETE FROM articles_entities WHERE article_id IN (SELECT id FROM articles WHERE url = %s)", (TEST_URL,))
            cur.execute("DELETE FROM articles_keywords WHERE article_id IN (SELECT id FROM articles WHERE url = %s)", (TEST_URL,))
            cur.execute("DELETE FROM articles_authors  WHERE article_id IN (SELECT id FROM articles WHERE url = %s)", (TEST_URL,))
            cur.execute("DELETE FROM articles WHERE url = %s", (TEST_URL,))

            # Asegura un run_id presente
            cur.execute(
                "INSERT INTO nlp_runs (run_id, date) VALUES (%s, NOW()) ON CONFLICT DO NOTHING",
                (TEST_RUN,),
            )

            # Inserta artículo base (schema v5: usar body_hash en vez de hash)
            cur.execute(
                """
                INSERT INTO articles (title, url, body, publication_date, body_hash, run_id)
                VALUES (%s, %s, %s, CURRENT_DATE, %s, %s)
                RETURNING id
                """,
                ("Artículo de test", TEST_URL, "Contenido de prueba", "test-body-hash-123", TEST_RUN),
            )
            article_id = cur.fetchone()[0]
    return article_id


def test_save_authors_inserta_y_relaciona(db_conn, test_article_id):
    autores = ["Gabriel Test", "Otro Autor"]
    with db_conn:
        with db_conn.cursor() as cur:
            save_authors(cur, test_article_id, autores)

    # Verificar relación y autores
    with db_conn.cursor() as cur:
        cur.execute(
            "SELECT a.name FROM authors a "
            "JOIN articles_authors aa ON aa.author_id = a.id "
            "WHERE aa.article_id = %s ORDER BY a.name",
            (test_article_id,),
        )
        rows = [r[0] for r in cur.fetchall()]
    assert rows == sorted(autores)


def test_save_keywords_inserta_y_relaciona_desde_string(db_conn, test_article_id):
    kws = "keyword1, palabra clave"
    with db_conn:
        with db_conn.cursor() as cur:
            save_keywords(cur, test_article_id, kws)

    with db_conn.cursor() as cur:
        cur.execute(
            "SELECT k.word FROM keywords k "
            "JOIN articles_keywords ak ON ak.keyword_id = k.id "
            "WHERE ak.article_id = %s ORDER BY k.word",
            (test_article_id,),
        )
        words = [r[0] for r in cur.fetchall()]
    assert words == ["keyword1", "palabra clave"]


def test_save_entities_inserta_y_relaciona(db_conn, test_article_id):
    ents = [{"text": "Chile", "label": "LOC"}]
    with db_conn:
        with db_conn.cursor() as cur:
            save_entities(cur, test_article_id, ents)

    with db_conn.cursor() as cur:
        cur.execute(
            "SELECT e.name, e.type FROM entities e "
            "JOIN articles_entities ae ON ae.entity_id = e.id "
            "WHERE ae.article_id = %s",
            (test_article_id,),
        )
        rows = cur.fetchall()
    assert rows == [("Chile", "LOC")]


def test_save_framing_direct_fields(db_conn, test_article_id):
    payload = {
        "ideological_frame": "neutral",
        "actors": ["gobierno"],
        "victims": ["ciudadanos"],
        "antagonists": ["corrupción"],
        "emotions": ["esperanza"],
        "summary": "El artículo describe un problema político.",
    }
    with db_conn:
        with db_conn.cursor() as cur:
            save_framing(cur, test_article_id, payload)

    with db_conn.cursor() as cur:
        cur.execute(
            "SELECT ideological_frame, actors, victims, antagonists, emotions, summary "
            "FROM framings WHERE article_id = %s",
            (test_article_id,),
        )
        row = cur.fetchone()
    assert row[0] == "neutral"
    assert row[1] == ["gobierno"]
    assert row[2] == ["ciudadanos"]
    assert row[3] == ["corrupción"]
    assert row[4] == ["esperanza"]
    assert isinstance(row[5], str) and "político" in row[5]


def test_save_framing_via_narrative_role(db_conn, test_article_id):
    """Cubre la ruta alternativa: narrative_role.actor/victim/antagonist."""
    payload = {
        "ideological_frame": "crítico",
        "narrative_role": {
            "actor": ["prensa"],
            "victim": ["público"],
            "antagonist": ["desinformación"],
        },
        "emotions": ["alarma"],
        "summary": "Se enmarca el fenómeno como una amenaza.",
    }
    with db_conn:
        with db_conn.cursor() as cur:
            save_framing(cur, test_article_id, payload)

    with db_conn.cursor() as cur:
        cur.execute(
            "SELECT ideological_frame, actors, victims, antagonists, emotions, summary "
            "FROM framings WHERE article_id = %s",
            (test_article_id,),
        )
        row = cur.fetchone()
    assert row[0] == "crítico"
    assert row[1] == ["prensa"]
    assert row[2] == ["público"]
    assert row[3] == ["desinformación"]
    assert row[4] == ["alarma"]
    assert isinstance(row[5], str) and "amenaza" in row[5]
