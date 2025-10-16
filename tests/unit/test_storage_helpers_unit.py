# tests/unit/test_storage_helpers_unit.py
from typing import Any, Iterable, List, Tuple
import pytest


from scrapy_project.storage_helpers import (
    save_keywords,
    save_entities,
    save_framing,
    store_article,
)

from scrapy_project.storage_helpers import save_authors, save_entities, save_framing

pytestmark = pytest.mark.unit

# ---- Fakes robustos para conexión/cursor (soportan context manager y llamadas directas) ----

class FakeCursor:
    def __init__(self):
        self.execute_calls: List[Tuple[str, Any]] = []
        self.executemany_calls: List[Tuple[str, Iterable[Any]]] = []
        self.fetchone_value: Tuple[Any, ...] | None = (123,)
        self.raise_on: str | None = None  # "execute"

    # Context manager
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        # No suprimir excepciones
        return False

    # API tipo psycopg2
    def execute(self, sql, params=None):
        if self.raise_on == "execute":
            raise RuntimeError("DB fail (execute)")
        self.execute_calls.append((sql, params))

    def executemany(self, sql, seq_of_params):
        # No la usa la impl actual, pero dejamos tracking por si cambia
        self.executemany_calls.append((sql, list(seq_of_params)))

    def fetchone(self):
        return self.fetchone_value


class FakeConn:
    def __init__(self, cursor: FakeCursor):
        self._cursor = cursor
        self.commit_called = False
        self.rollback_called = False

    # Soporta BOTH: "with conn.cursor() as cur" y "cur = conn.cursor()"
    def cursor(self):
        return self._cursor

    def commit(self):
        self.commit_called = True

    def rollback(self):
        self.rollback_called = True


def _fake_conn():
    cur = FakeCursor()
    # En "with conn.cursor() as cur:", Python llamará __enter__/__exit__ en el cursor devuelto.
    # En "cur = conn.cursor()", el cursor igual sirve.
    conn = FakeConn(cur)
    return conn, cur


# ----------------- TESTS -----------------

# save_keywords(conn, article_id, keywords_string_comas)

def test_save_keywords_vacio_no_ejecuta():
    conn, cur = _fake_conn()
    save_keywords(conn, 123, "")
    assert not cur.execute_calls and not cur.executemany_calls
    assert not conn.commit_called and not conn.rollback_called

def test_save_keywords_espacios_no_ejecuta():
    conn, cur = _fake_conn()
    save_keywords(conn, 123, "   ,  , ")
    assert not cur.execute_calls and not cur.executemany_calls
    assert not conn.commit_called and not conn.rollback_called

def test_save_keywords_inserta_parametrizado():
    conn, cur = _fake_conn()
    save_keywords(conn, 1, "Chile,  Chile ,  Política")
    # Debe haber ejecutado algo (execute o executemany)
    did_exec = bool(cur.execute_calls or cur.executemany_calls)
    assert did_exec, "Se esperaba una inserción (execute o executemany)"
    # Conexión -> la v2 hace commit (compatibilidad)
    assert conn.commit_called

def test_save_keywords_error_hace_rollback():
    conn, cur = _fake_conn()
    cur.raise_on = "execute"  # la impl actual usa execute()
    with pytest.raises(RuntimeError):
        save_keywords(conn, 1, "A, B")
    assert conn.rollback_called and not conn.commit_called


# save_entities(conn, article_id, entities_list)

def test_save_entities_vacia_no_ejecuta():
    conn, cur = _fake_conn()
    save_entities(conn, 1, [])
    assert not cur.execute_calls and not cur.executemany_calls
    assert not conn.commit_called and not conn.rollback_called


# save_framing(conn, article_id, framing_dict)

def test_save_framing_guarda_estructura_basica():
    conn, cur = _fake_conn()
    framing = {
        "ideological_frame": "x",
        "narrative_role": {"actor": ["a"], "victim": [], "antagonist": []},
        "emotions": ["y"],
        "summary": "s",
    }
    save_framing(conn, 9, framing)
    assert (cur.execute_calls or cur.executemany_calls), "Se esperaba inserción"
    assert conn.commit_called


# store_article(conn, item_dict) -> id

def test_store_article_retorna_id_int():
    conn, cur = _fake_conn()
    cur.fetchone_value = (456,)
    # store_article requiere: url, title, body, publication_date, hash, run_id
    item = {
        "url": "u",
        "title": "t",
        "body": "b",
        "publication_date": "2025-01-01",
        "hash": "h",
        "run_id": "r",
    }
    out_id = store_article(conn, item)
    assert out_id == 456
    assert conn.commit_called

def test_store_article_falla_hace_rollback():
    conn, cur = _fake_conn()
    cur.raise_on = "execute"
    with pytest.raises(Exception):
        # faltan claves requeridas (o falla execute) -> excepción y rollback
        store_article(conn, {"url": "u"})
    assert conn.rollback_called and not conn.commit_called


# Reusa tus FakeConn/FakeCursor del archivo actual

class _CurErrExecute:
    def __init__(self): self._raised = False
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def execute(self, *a, **kw): raise RuntimeError("execute boom")
    def fetchone(self): return (1,)

class _ConnWrap:
    def __init__(self, cur):
        self._cur = cur; self.commit_called=False; self.rollback_called=False
    def cursor(self): return self._cur
    def commit(self): self.commit_called=True
    def rollback(self): self.rollback_called=True

def test_save_authors_error_rollback_with_conn():
    conn = _ConnWrap(_CurErrExecute())
    with pytest.raises(RuntimeError):
        save_authors(conn, 1, ["A"])
    assert conn.rollback_called and not conn.commit_called

def test_save_entities_error_rollback_with_conn():
    conn = _ConnWrap(_CurErrExecute())
    with pytest.raises(RuntimeError):
        save_entities(conn, 1, [{"text":"X","label":"Y"}])
    assert conn.rollback_called and not conn.commit_called

def test_save_framing_error_rollback_with_conn():
    conn = _ConnWrap(_CurErrExecute())
    with pytest.raises(RuntimeError):
        save_framing(conn, 1, {"ideological_frame":"x"})
    assert conn.rollback_called and not conn.commit_called