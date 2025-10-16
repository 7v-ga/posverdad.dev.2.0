import pytest
from unittest.mock import MagicMock
from scrapy_project.storage_helpers import store_article

pytestmark = pytest.mark.unit

@pytest.fixture
def mock_conn():
    """
    Conexión y cursor mockeados:
    - conn.cursor() devuelve un objeto 'cur' que soporta execute(), fetchone() y también __enter__/__exit__.
    - fetchone() devuelve (1,) para simular el RETURNING id.
    """
    cur = MagicMock(name="cursor")
    cur.fetchone.return_value = (1,)
    cur.__enter__.return_value = cur   # por si algún código usa 'with conn.cursor() as cur:'
    cur.__exit__.return_value = False

    conn = MagicMock(name="conn")
    conn.cursor.return_value = cur     # store_article usará este 'cur' directamente
    return conn

def test_store_article_basic_insert(mock_conn):
    article = {
        "title": "Artículo simulado",
        "url": "https://example.com/test",
        "publication_date": "2025-07-08",
        "body": "Texto de ejemplo.",
        "meta_keywords": "test, ejemplo",
        "author": "María Prueba",
        "run_id": "test_run_mocked",
        "hash": "hash-mock-test",
        "sentiment": {"label": "POS", "probs": {"POS": 0.7, "NEU": 0.2, "NEG": 0.1}},
        "entities": [{"text": "Chile", "label": "LOC"}],
        "framing": {
            "ideological_frame": "progresista",
            "actors": ["gobierno"],
            "victims": ["pueblo"],
            "antagonists": ["oposición"],
            "emotions": ["esperanza"],
            "summary": "El artículo describe una narrativa de cambio.",
        },
    }

    article_id = store_article(mock_conn, article)
    assert article_id == 1

    # Opcional: algunas verificaciones útiles
    cur = mock_conn.cursor.return_value
    assert cur.execute.call_count >= 1  # se ejecutó al menos un INSERT
    # Como pasamos 'conn', la v2 hace commit al final (compatibilidad)
    assert mock_conn.commit.called
