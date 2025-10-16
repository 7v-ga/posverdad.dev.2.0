# tests/unit/test_pipeline_dates_normalization.py
from types import SimpleNamespace
from scrapy_project import pipelines as pl

class FakeCursor:
    def __init__(self):
        self.closed = False
        self.queries = []

    # Context manager protocol
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        self.close()

    # Cursor API
    def execute(self, q, params=None):
        self.queries.append((q, params))
    def fetchone(self):
        return None
    def close(self):
        self.closed = True

class DummyConn:
    """Conexión falsa con protocolo de contexto y cursor con context manager."""
    def __init__(self):
        self._cur = FakeCursor()
    def __enter__(self):
        return self
    def __exit__(self, *exc):
        return False
    def cursor(self):
        # Importante: devolver un objeto que soporte __enter__/__exit__
        return FakeCursor()

def make_pipeline(monkeypatch):
    p = pl.ScrapyProjectPipeline()
    # Evitar DB real
    p.conn = DummyConn()
    # Evitar dedupe real
    monkeypatch.setattr(p, "_check_duplicates", lambda cur, item: None)
    # Evitar NLP real
    p.nlp = SimpleNamespace(analyze=lambda txt: {})
    # Evitar insert real (usa el nombre importado dentro de pipelines)
    monkeypatch.setattr(pl, "store_article", lambda cur, item: 123)
    return p

def test_dates_when_published_at_present(monkeypatch):
    p = make_pipeline(monkeypatch)
    item = {
        "url": "https://x/y",
        "title": "t",
        # cuerpo ≥ 50 chars para no gatillar DropItem (MIN_BODY_LEN=50)
        "body": "cuerpo " * 10,  # ~70+ caracteres
        "published_at": "2024-09-05T10:20:30Z",
        "publication_date": "2024-09-04",
    }
    out = p.process_item(item, spider=SimpleNamespace(name="s"))
    # published_at domina y se proyecta a publication_date[:10]
    assert out["publication_date"] == "2024-09-05"
    assert out["published_at"] == "2024-09-05T10:20:30Z"

def test_dates_when_only_publication_date(monkeypatch):
    p = make_pipeline(monkeypatch)
    item = {
        "url": "https://x/y",
        "title": "t",
        # cuerpo ≥ 50 chars para no gatillar DropItem (MIN_BODY_LEN=50)
        "body": "contenido " * 6,  # >= 54 caracteres aprox.
        "publication_date": "2024-09-01",
    }
    out = p.process_item(item, spider=SimpleNamespace(name="s"))
    # si solo hay publication_date, rellena published_at a medianoche Z
    assert out["published_at"].startswith("2024-09-01T00:00:00Z")
