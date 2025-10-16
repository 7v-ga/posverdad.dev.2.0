from scrapy_project.storage_helpers import upsert_categories, link_article_categories, save_categories_and_link

class CatDB:
    def __init__(self):
        self.cat = {}          # name -> id
        self.next_id = 1
        self.links = set()     # (article_id, category_id)
        self._row = None

    def cursor(self): return self
    def commit(self): pass
    def rollback(self): pass
    def close(self): pass

    def execute(self, sql, params=None):
        low = sql.lower().strip()

        if low.startswith("insert into categories"):
            name = params[0]
            if name not in self.cat:
                self.cat[name] = self.next_id
                self.next_id += 1
            self._row = (self.cat[name],)
            return

        if low.startswith("insert into articles_categories"):
            a_id, c_id = params
            self.links.add((a_id, c_id))
            return

        self._row = None

    def fetchone(self): return self._row


def test_upsert_categories_and_link():
    db = CatDB()
    cur = db.cursor()

    ids = upsert_categories(cur, ["Política", "Economía", "Política"])
    assert len(ids) == 3  # devuelve id por cada input, incluso repetido
    assert set(db.cat.keys()) == {"Política", "Economía"}

    link_article_categories(cur, 7, set(ids))
    # Enlaza únicos
    assert {cid for (_a, cid) in db.links} == set(db.cat.values())


def test_save_categories_and_link_helper():
    db = CatDB()
    save_categories_and_link(db, 11, ["País", "Opinión", "País"])
    assert set(db.cat.keys()) == {"País", "Opinión"}
    # vínculos únicos
    assert {cid for (_a, cid) in db.links} == set(db.cat.values())
