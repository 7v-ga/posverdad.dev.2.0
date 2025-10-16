import re
from types import SimpleNamespace
from scrapy_project.storage_helpers import save_authors

class CaptureCursor:
    def __init__(self):
        self.closed = False
        self.executed = []  # (sql, params)

    def __enter__(self): return self
    def __exit__(self, *exc): self.close()

    def execute(self, sql, params=None):
        self.executed.append((sql, params))

    def fetchone(self):
        # Simula que no existe y luego devuelve el último insertado con id finto
        last = self.executed[-1][1] if self.executed else None
        # Para SELECT id FROM authors ... devolvemos una "fila"
        if self.executed and "SELECT id FROM authors" in self.executed[-1][0]:
            return (1,)
        # Para RETURNING id...
        if self.executed and "RETURNING id" in self.executed[-1][0]:
            return (1,)
        return None

    def close(self):
        self.closed = True

class CaptureConn:
    def __init__(self):
        self.cur = CaptureCursor()
        self.commit_called = False
        self.rollback_called = False

    def cursor(self):
        # ← SIEMPRE devolver el MISMO cursor
        return self.cur

    def commit(self):
        self.commit_called = True

    def rollback(self):
        self.rollback_called = True

def _extracted_author_names(exec_list):
    names = []
    for sql, params in exec_list:
        if isinstance(sql, str) and "INSERT INTO authors (name)" in sql and params:
            names.append(params[0])
    return names

def test_save_authors_splits_list_elements_by_commas():
    conn = CaptureConn()
    save_authors(conn, article_id=123, author_value=["Ana,  Ben", "Carlos"])

    # Recupera los nombres insertados del cursor PERSISTENTE
    names = _extracted_author_names(conn.cur.executed)

    assert set(["Ana", "Ben", "Carlos"]).issubset(set(names))

