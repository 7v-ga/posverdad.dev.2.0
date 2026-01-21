# tests/unit/test_storage_db_branching.py
import pytest
from scrapy_project.storage_helpers import save_keywords

class KWConnOK:
    """Conexión que expone cursor(); cubre _as_cursor → manage_tx=True."""
    def __init__(self):
        self._cur = KWCursorOK()
        self.commits = 0
        self.rollbacks = 0
    def cursor(self): return self._cur
    def commit(self): self.commits += 1
    def rollback(self): self.rollbacks += 1

class KWCursorOK:
    """
    Cursor que modela:
      - SELECT to_regclass(...)
      - INSERT keywords ... RETURNING id
      - SELECT id FROM keywords ...
      - INSERT articles_keywords ...
    """
    def __init__(self):
        self.kw = {}  # keyword -> id
        self._row = None
        self._next = 1

    def execute(self, sql, params=None):
        low = " ".join(str(sql).strip().lower().split())

        # Schema probing
        if low.startswith("select to_regclass"):
            # Simulamos que existe (devuelve nombre de tabla)
            self._row = ("public.keywords",)
            return

        # INSERT ... RETURNING id (preferente)
        if low.startswith("insert into keywords") and "returning id" in low:
            w = params[0]
            if w not in self.kw:
                self.kw[w] = self._next
                self._next += 1
            self._row = (self.kw[w],)
            return

        # INSERT ... DO NOTHING (sin returning)
        if low.startswith("insert into keywords") and "do nothing" in low:
            w = params[0]
            if w not in self.kw:
                self.kw[w] = self._next
                self._next += 1
            self._row = None
            return

        # SELECT id
        if low.startswith("select id from keywords"):
            w = params[0]
            kid = self.kw.get(w)
            self._row = (kid,) if kid else None
            return

        # Link table insert
        if low.startswith("insert into articles_keywords"):
            self._row = None
            return

        self._row = None

    def fetchone(self):
        return self._row

def test_save_keywords_as_connection_ok():
    db = KWConnOK()
    save_keywords(db, 1, ["a", "b"])
    assert db.commits == 1
    assert db.rollbacks == 0
    assert set(db._cur.kw.keys()) >= {"a", "b"}

class KWConnFail(KWConnOK):
    """Fuerza excepción en un punto no-ignorable para cubrir rollback + RuntimeError."""
    def __init__(self):
        super().__init__()
        self._cur = KWCursorFail()

class KWCursorFail(KWCursorOK):
    def execute(self, sql, params=None):
        low = " ".join(str(sql).strip().lower().split())
        # Romper en el INSERT a keywords con RETURNING (debe propagar como RuntimeError)
        if low.startswith("insert into keywords") and "returning id" in low:
            raise RuntimeError("boom")
        return super().execute(sql, params)

def test_save_keywords_rollback_on_error():
    db = KWConnFail()
    with pytest.raises(RuntimeError):
        save_keywords(db, 1, ["x", "y"])
    assert db.rollbacks == 1
    assert db.commits == 0

def test_save_keywords_as_cursor_ok():
    cur = KWCursorOK()
    save_keywords(cur, 99, ["k"])
    assert "k" in cur.kw
