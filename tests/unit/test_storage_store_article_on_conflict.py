from scrapy_project.storage_helpers import store_article

class ConnUpsert:
    def __init__(self):
        self.cur = CurUpsert()
        self.commits = 0
        self.rollbacks = 0
    def cursor(self): return self.cur
    def commit(self): self.commits += 1
    def rollback(self): self.rollbacks += 1

class CurUpsert:
    def __init__(self):
        # Pre-cargamos la fuente por dominio para que no intente insertarla
        self.sources_by_domain = {"elmostrador.cl": 7}
        self.articles_by_url = {}   # url -> id
        self._next_article_id = 500
        self._row = None

    def execute(self, sql, params=None):
        low = sql.lower().strip()

        # Fuentes (resolver por dominio)
        if low.startswith("select id from sources where domain"):
            dom = params[0]
            rid = self.sources_by_domain.get(dom)
            self._row = (rid,) if rid else None
            return

        # INSERT INTO articles (...) ON CONFLICT (url) DO UPDATE ... RETURNING id;
        if low.startswith("insert into articles"):
            url = params[0]
            if url in self.articles_by_url:
                # Conflicto → devolvemos el ID existente (ruta de upsert)
                self._row = (self.articles_by_url[url],)
            else:
                aid = self._next_article_id
                self._next_article_id += 1
                self.articles_by_url[url] = aid
                self._row = (aid,)
            return

        # Enlace categories (si viniera) — ignorar si no se usa
        if low.startswith("insert into articles_categories"):
            self._row = None
            return

        # No usado en este test
        self._row = None

    def fetchone(self):
        return self._row

def test_store_article_upsert_conflict_same_canonical_url():
    db = ConnUpsert()
    item = {
        # Trae utm + slash final → normalize_url lo deja canónico
        "url": "https://www.elmostrador.cl/noticias/pais/2020/01/02/post/?utm_source=news",
        "title": "t",
        "body": "b",
        "publication_date": "2020-01-02",
        "source": "elmostrador",
        "domain": "elmostrador.cl",
        # Evitamos ramas de relaciones auxiliares para aislar ON CONFLICT:
        "meta_keywords": None,
        "authors": None,
        "categories": None,
        "entities": None,
        "framing": None,
        "run_id": None,
    }

    # Primer insert
    a1 = store_article(db, item)
    # Segundo llamado con misma URL (se canoniciza igual) → debe activar ON CONFLICT
    a2 = store_article(db, item)

    assert a1 == a2
    # Comprobamos que se usó URL canónica como clave:
    assert "https://elmostrador.cl/noticias/pais/2020/01/02/post" in db.cur.articles_by_url
    # Commit realizado
    assert db.commits == 2
    assert db.rollbacks == 0
