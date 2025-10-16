import pytest
from scrapy_project.storage_helpers import save_keywords, save_entities, save_framing, store_article

pytestmark = pytest.mark.unit


# ------------ Fakes robustos (soportan 'with conn.cursor()' y llamadas directas) -------------
class _Cursor:
    def __init__(self, fetch_id=123):
        self.fetch_id = fetch_id
        self.executed = []
    def execute(self, *args, **kwargs):
        self.executed.append((args, kwargs))
    def fetchone(self):
        return [self.fetch_id]
    def close(self):
        pass
    def __enter__(self): 
        return self
    def __exit__(self, *a): 
        return False  # no suprime excepciones

class _Conn:
    def __init__(self, cursor=None):
        self._cur = cursor or _Cursor()
        self.commit_called = False
        self.rollback_called = False
    def cursor(self):
        return self._cur
    def commit(self): 
        self.commit_called = True
    def rollback(self): 
        self.rollback_called = True


@pytest.fixture
def mock_cursor():
    return _Cursor()

@pytest.fixture
def mock_conn(mock_cursor):
    return _Conn(mock_cursor)


# ---------------------------------- Tests de entradas vacías ----------------------------------

def test_save_keywords_empty(mock_conn):
    # no debería ejecutar SQL ni fallar
    save_keywords(mock_conn, 1, "")
    save_keywords(mock_conn, 1, None)

def test_save_entities_empty(mock_conn):
    save_entities(mock_conn, 1, [])
    save_entities(mock_conn, 1, None)

def test_save_framing_empty(mock_conn):
    save_framing(mock_conn, 1, {})


# ------------------------------- store_article con mínimos opcionales -------------------------------

def test_store_article_missing_optional_fields_with_conn(mock_conn):
    article = {
        "url": "https://example.com/edge-case",
        "title": "Edge Case Article",
        "body": "Texto sin categoría ni fuente",
        "publication_date": "2025-01-01",
        "hash": "hash-edge",
        "run_id": "test_run_edge"
    }
    result = store_article(mock_conn, article)  # pasa CONNECTION (compat)
    assert isinstance(result, int)

def test_store_article_missing_optional_fields_with_cursor(mock_cursor):
    article = {
        "url": "https://example.com/edge-case",
        "title": "Edge Case Article",
        "body": "Texto sin categoría ni fuente",
        "publication_date": "2025-01-01",
        "hash": "hash-edge",
        "run_id": "test_run_edge"
    }
    result = store_article(mock_cursor, article)  # pasa CURSOR (nuevo flujo)
    assert isinstance(result, int)
