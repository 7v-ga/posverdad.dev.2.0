# tests/unit/test_pipeline_dates_normalization.py
from types import SimpleNamespace
from contextlib import contextmanager
import scrapy_project.pipelines as pl


@contextmanager
def _noop_tx():
    yield


class DummyCursor:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        # no suprimir excepciones
        return False

    def execute(self, *args, **kwargs):
        return None

    def fetchone(self):
        return None


class DummyConn:
    """Conexión falsa con cursor() usable en `with self.conn.cursor() as cur:`."""
    def cursor(self):
        return DummyCursor()


def make_pipeline(monkeypatch):
    p = pl.ScrapyProjectPipeline()

    # Evitar DB real
    p.conn = DummyConn()

    # Neutralizar infraestructura ajena al test (tx/rollback/reconnect)
    monkeypatch.setattr(p, "_ensure_conn", lambda: None, raising=False)
    monkeypatch.setattr(p, "_rollback_if_needed", lambda *a, **k: None, raising=False)
    monkeypatch.setattr(p, "_tx_ctx", lambda: _noop_tx(), raising=False)

    # Evitar dedupe real y NLP real
    monkeypatch.setattr(p, "_check_duplicates", lambda cur, item: None, raising=False)
    p.nlp = SimpleNamespace(analyze=lambda txt: {})

    # Evitar persistencia real; soportar kwargs
    monkeypatch.setattr(pl, "store_article", lambda cur, item, **kw: (123, True))

    return p


def test_dates_when_published_at_present(monkeypatch):
    p = make_pipeline(monkeypatch)
    item = {
        "url": "https://x/y",
        "title": "t",
        "body": "cuerpo " * 10,
        "published_at": "2024-09-05T10:20:30Z",
        "publication_date": "2024-09-04",
    }
    out = p.process_item(item, spider=SimpleNamespace(name="s"))
    assert out["publication_date"] == "2024-09-05"
    assert out["published_at"] == "2024-09-05T10:20:30Z"


def test_dates_when_only_publication_date(monkeypatch):
    p = make_pipeline(monkeypatch)
    item = {
        "url": "https://x/y",
        "title": "t",
        "body": "contenido " * 6,
        "publication_date": "2024-09-01",
    }
    out = p.process_item(item, spider=SimpleNamespace(name="s"))
    assert out["publication_date"] == "2024-09-01"
    assert out["published_at"] == "2024-09-01T00:00:00Z"
