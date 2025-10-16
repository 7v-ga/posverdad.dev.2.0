# tests/unit/test_storage_save_preprocessed_unit.py
import pytest
from scrapy_project.storage import save_preprocessed_data

pytestmark = pytest.mark.unit


class FakeCursor:
    def __init__(self, raise_on_execute: bool = False):
        self.execute_calls = []
        self.raise_on_execute = raise_on_execute
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def execute(self, sql, params=None):
        if self.raise_on_execute:
            raise RuntimeError("DB fail (execute)")
        self.execute_calls.append((sql, params))
    def fetchone(self):
        return None


class FakeConn:
    def __init__(self, cur: FakeCursor):
        self._cur = cur
        self.commit_called = False
        self.rollback_called = False
    def cursor(self): return self._cur
    def commit(self): self.commit_called = True
    def rollback(self): self.rollback_called = True


def test_save_preprocessed_with_cursor_no_commit():
    cur = FakeCursor()
    save_preprocessed_data(123, {"x": 1}, cur)
    assert cur.execute_calls, "Debe ejecutar UPDATE"
    # Con cursor no hay control de transacción aquí (sin commit/rollback)


def test_save_preprocessed_with_conn_commits():
    cur = FakeCursor()
    conn = FakeConn(cur)
    save_preprocessed_data(123, {"x": 1}, conn)
    assert cur.execute_calls
    assert conn.commit_called and not conn.rollback_called


def test_save_preprocessed_with_conn_error_rolls_back():
    cur = FakeCursor(raise_on_execute=True)
    conn = FakeConn(cur)
    with pytest.raises(RuntimeError):
        save_preprocessed_data(123, {"x": 1}, conn)
    assert conn.rollback_called and not conn.commit_called


def test_save_preprocessed_with_cursor_error_bubbles():
    cur = FakeCursor(raise_on_execute=True)
    with pytest.raises(RuntimeError):
        save_preprocessed_data(123, {"x": 1}, cur)
    # No hay rollback aquí porque no hay conexión gestionando transacción
