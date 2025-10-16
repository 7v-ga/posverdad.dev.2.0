from scrapy_project.storage_helpers import save_keywords

class KWDB:
    def __init__(self):
        self.kw = {}                 # word -> id
        self.next_id = 1
        self.ak = set()              # (article_id, keyword_id)
        self._row = None

    def cursor(self): return self
    def commit(self): pass
    def rollback(self): pass
    def close(self): pass

    def execute(self, sql, params=None):
        low = sql.lower().strip()
        if low.startswith("insert into keywords"):
            word = params[0]
            if word not in self.kw:
                self.kw[word] = self.next_id
                self.next_id += 1
            # RETURNING id
            if "returning id" in low:
                self._row = (self.kw[word],)
            return
        if low.startswith("select id from keywords where word"):
            self._row = (self.kw.get(params[0]),) if params[0] in self.kw else None
            return
        if low.startswith("insert into articles_keywords"):
            a_id, k_id = params
            self.ak.add((a_id, k_id))
            return
        self._row = None

    def fetchone(self): return self._row


def test_save_keywords_explode_and_dedup():
    db = KWDB()
    article_id = 5

    # separadores , ; | / y espacios
    save_keywords(db, article_id, "k1, k2; k3 | k2 / k4")
    # repetir y en lista
    save_keywords(db, article_id, ["k1, k5", "k3", "k5"])

    # Debe haber 5 términos únicos: k1..k5
    assert set(db.kw.keys()) == {"k1", "k2", "k3", "k4", "k5"}

    # Relaciones únicas
    expected_ids = {db.kw[k] for k in ["k1", "k2", "k3", "k4", "k5"]}
    assert {kid for (_a, kid) in db.ak} == expected_ids
