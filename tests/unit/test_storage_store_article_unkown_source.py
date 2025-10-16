from scrapy_project.storage_helpers import store_article

class ConnUnknown:
    def __init__(self):
        self.cur = CurUnknown(self)
        self.commits = 0
    def cursor(self): return self.cur
    def commit(self): self.commits += 1
    def rollback(self): pass

class CurUnknown:
    def __init__(self, parent):
        self.parent = parent
        self.sources_by_name = {}
        self.articles = {}
        self._row = None
        self._next_article_id = 1000
    def execute(self, sql, params=None):
        low = sql.lower().strip()
        # SELECT id FROM sources WHERE domain = %s LIMIT 1;  → no domain
        if low.startswith("select id from sources where domain"):
            self._row = None; return
        # SELECT id FROM sources WHERE name = %s LIMIT 1;    → 'unknown' no existe
        if low.startswith("select id from sources where name"):
            name = params[0]
            self._row = (self.sources_by_name.get(name),) if name in self.sources_by_name else None
            return
        # INSERT INTO sources (name, domain) VALUES (%s, %s) RETURNING id;
        if low.startswith("insert into sources"):
            name, domain = params
            self.sources_by_name[name] = len(self.sources_by_name) + 1
            self._row = (self.sources_by_name[name],)
            return
        # INSERT INTO articles (...) ON CONFLICT (url) DO UPDATE ... RETURNING id;
        if low.startswith("insert into articles"):
            url = params[0]
            if url not in self.articles:
                self.articles[url] = self._next_article_id
                self._next_article_id += 1
            self._row = (self.articles[url],)
            return
        self._row = None
    def fetchone(self): return self._row

def test_store_article_creates_unknown_source_when_absent():
    db = ConnUnknown()
    item = {
        "url": "https://ex.com/news/2020/01/02/post",
        "title": "t",
        "body": "b",
        "publication_date": "2020-01-02",
        # sin source, sin domain
        "meta_keywords": None,   # evita save_keywords
        "authors": None,         # evita save_authors
        "categories": None,      # evita save_categories...
        "entities": None,
        "framing": None,
    }
    art_id = store_article(db, item)
    assert art_id >= 1000
    # Se creó fuente usando el dominio derivado de la URL
    assert "ex.com" in db.cur.sources_by_name
    assert db.commits == 1
