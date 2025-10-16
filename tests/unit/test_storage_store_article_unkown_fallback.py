from scrapy_project.storage_helpers import store_article

class ConnUnknown:
    def __init__(self):
        self.cur = CurUnknown()
        self.commits = 0
    def cursor(self): return self.cur
    def commit(self): self.commits += 1
    def rollback(self): pass

class CurUnknown:
    def __init__(self):
        self.sources_by_name = {}
        self.articles = {}
        self._row = None
        self._next_article_id = 1
    def execute(self, sql, params=None):
        low = sql.lower().strip()
        if low.startswith("select id from sources where domain"):
            # No hay dominio parseable en este caso → None
            self._row = None; return
        if low.startswith("select id from sources where name"):
            name = params[0]
            self._row = (self.sources_by_name.get(name),) if name in self.sources_by_name else None
            return
        if low.startswith("insert into sources"):
            name, domain = params
            # Guardará 'unknown'
            self.sources_by_name[name] = len(self.sources_by_name) + 1
            self._row = (self.sources_by_name[name],)
            return
        if low.startswith("insert into articles"):
            url = params[0]
            if url not in self.articles:
                self.articles[url] = self._next_article_id
                self._next_article_id += 1
            self._row = (self.articles[url],)
            return
        self._row = None
    def fetchone(self): return self._row

def test_store_article_fallback_unknown_when_no_domain():
    db = ConnUnknown()
    item = {
        "url": "nota-sin-dominio-y-sin-esquema",  # no parseable host
        "title": "t",
        "body": "b",
        "publication_date": "2020-01-02",
        "meta_keywords": None,
        "authors": None,
        "categories": None,
        "entities": None,
        "framing": None,
    }
    art_id = store_article(db, item)
    assert art_id >= 1
    assert "unknown" in db.cur.sources_by_name
    assert db.commits == 1
