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
    """Cursor simple que soporta el flujo de save_keywords sin error."""
    def __init__(self):
        self.kw = {}  # word -> id
        self._row = None
        self._next = 1
    def execute(self, sql, params=None):
        low = sql.lower()
        if low.startswith("insert into keywords") and "do nothing" in low:
            w = params[0]
            self.kw.setdefault(w, self._next); self._next = max(self._next, self.kw[w]+1)
            self._row = None
        elif low.startswith("select id from keywords"):
            w = params[0]
            kid = self.kw.get(w)
            self._row = (kid,) if kid else None
        elif low.startswith("insert into keywords") and "returning id" in low:
            w = params[0]
            self.kw.setdefault(w, self._next); self._next = max(self._next, self.kw[w]+1)
            self._row = (self.kw[w],)
        elif low.startswith("insert into articles_keywords"):
            self._row = None
        else:
            self._row = None
    def fetchone(self): return self._row

def test_save_keywords_as_connection_ok():
    db = KWConnOK()            # conexión
    save_keywords(db, 1, ["a", "b"])
    assert db.commits == 1     # se hizo commit (manage_tx=True)
    assert db.rollbacks == 0

class KWConnFail(KWConnOK):
    """Fuerza excepción a mitad de ciclo para cubrir rollback."""
    def __init__(self): super().__init__(); self._cur = KWCursorFail(self)

class KWCursorFail(KWCursorOK):
    def __init__(self, parent): super().__init__(); self.parent = parent; self.calls = 0
    def execute(self, sql, params=None):
        self.calls += 1
        # Lanza en la 3ª llamada para entrar al except de save_keywords
        if self.calls == 3:
            raise RuntimeError("boom")
        return super().execute(sql, params)

def test_save_keywords_rollback_on_error():
    db = KWConnFail()
    with pytest.raises(RuntimeError):
        save_keywords(db, 1, ["x", "y"])
    assert db.rollbacks == 1
    # No hay commit
    assert db.commits == 0

def test_save_keywords_as_cursor_ok():
    # _as_cursor detecta cursor directo (manage_tx=False, no commit/rollback)
    cur = KWCursorOK()
    save_keywords(cur, 99, ["k"])
    # simple smoke: la palabra quedó registrada
    assert "k" in cur.kw
