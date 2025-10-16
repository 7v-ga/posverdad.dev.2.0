import pytest
from types import SimpleNamespace
from scrapy_project.storage import save_preprocessed_data

class FakeCursor:
    def __init__(self, fail=False):
        self.queries = []
        self.closed = False
        self.fail = fail
    def execute(self, q, params):
        self.queries.append((q, params))
        if self.fail:
            raise RuntimeError("boom")
    def fetchone(self): return None
    def close(self): self.closed = True

class FakeConn:
    def __init__(self, fail=False):
        self.fail = fail
        self.commit_called = False
        self.rollback_called = False
        self.cur = FakeCursor(fail=fail)
    def cursor(self): return self.cur
    def commit(self): self.commit_called = True
    def rollback(self): self.rollback_called = True

def test_save_preprocessed_with_cursor_ok():
    cur = FakeCursor()
    save_preprocessed_data(article_id=1, preprocessed={"x": 1}, db=cur)
    # No cierra cursor propio ni comitea/rollbackea (modo cursor)
    assert any("UPDATE articles SET preprocessed_data" in q for (q, _p) in cur.queries)
    assert cur.closed is False

def test_save_preprocessed_with_connection_ok():
    conn = FakeConn(fail=False)
    save_preprocessed_data(article_id=2, preprocessed={"y": 2}, db=conn)
    # Con conexión: hace commit y cierra el cursor
    assert conn.commit_called is True
    assert conn.cur.closed is True

def test_save_preprocessed_with_connection_failure_rolls_back():
    conn = FakeConn(fail=True)
    with pytest.raises(RuntimeError):
        save_preprocessed_data(article_id=3, preprocessed={"z": 3}, db=conn)
    assert conn.rollback_called is True
    assert conn.cur.closed is True
