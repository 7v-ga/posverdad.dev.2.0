import types
import hashlib
import pytest

from scrapy_project.storage_helpers import (
    store_article,
    normalize_url,
    _as_nullable_float,
    _normalize_meta_keywords_for_articles_field,
)

class FakeCursor:
    def __init__(self):
        self.calls = []
        self._last_sql = None
        self._last_params = None
        # Fuentes
        self.sources_by_domain = {"elmostrador.cl": 10}
        self.sources_by_name = {}
        # Artículos
        self.articles_by_url = {}  # url -> id
        self._next_article_id = 100
        # 🔸 Keywords
        self.keywords_by_word = {}  # word -> id
        self._next_keyword_id = 1
        self.articles_keywords = set()  # (article_id, keyword_id)

        self._last_row = None

    def execute(self, sql, params=None):
        self.calls.append((sql.strip(), params))
        self._last_sql = sql
        self._last_params = params

        low = sql.lower().strip()

        # ----- SOURCES -----
        if low.startswith("select id from sources where domain"):
            dom = params[0]
            rid = self.sources_by_domain.get(dom)
            self._last_row = (rid,) if rid else None
            return
        if low.startswith("select id from sources where name"):
            name = params[0]
            rid = self.sources_by_name.get(name)
            self._last_row = (rid,) if rid else None
            return
        if low.startswith("insert into sources"):
            name, domain = params
            rid = len(self.sources_by_domain) + len(self.sources_by_name) + 1
            if domain:
                self.sources_by_domain[domain] = rid
            elif name:
                self.sources_by_name[name] = rid
            self._last_row = (rid,)
            return

        # ----- ARTICLES (INSERT ... ON CONFLICT (url) DO UPDATE ... RETURNING id) -----
        if low.startswith("insert into articles"):
            url = params[0]
            if url in self.articles_by_url:
                self._last_row = (self.articles_by_url[url],)
            else:
                aid = self._next_article_id
                self._next_article_id += 1
                self.articles_by_url[url] = aid
                self._last_row = (aid,)
            return

        # ----- KEYWORDS -----
        if low.startswith("insert into keywords") and "on conflict (word) do nothing" in low:
            word = params[0]
            if word not in self.keywords_by_word:
                self.keywords_by_word[word] = self._next_keyword_id
                self._next_keyword_id += 1
            self._last_row = None
            return

        if low.startswith("select id from keywords where word"):
            word = params[0]
            kid = self.keywords_by_word.get(word)
            self._last_row = (kid,) if kid else None
            return

        if low.startswith("insert into keywords") and "returning id" in low:
            word = params[0]
            if word not in self.keywords_by_word:
                self.keywords_by_word[word] = self._next_keyword_id
                self._next_keyword_id += 1
            self._last_row = (self.keywords_by_word[word],)
            return

        if low.startswith("insert into articles_keywords"):
            a_id, k_id = params
            self.articles_keywords.add((a_id, k_id))
            self._last_row = None
            return

        # Default
        self._last_row = None

    def fetchone(self):
        return self._last_row

    def close(self):
        pass



class FakeConn:
    def __init__(self):
        self.cur = FakeCursor()
        self._commits = 0
    def cursor(self):
        return self.cur
    def commit(self):
        self._commits += 1
    def rollback(self):
        pass


def test_normalize_url_basic():
    u = "http://www.elmostrador.cl/foo/?utm_source=news&x=1#frag"
    out = normalize_url(u)
    assert out == "http://elmostrador.cl/foo?x=1"  # sin www, sin utm, sin fragment


@pytest.mark.parametrize("inp, expected", [
    (None, None),
    ("", None),
    ("   ", None),
    ("0.0", 0.0),
    ("NaN", None),
    (float("inf"), None),
    ({"value": "1.25"}, 1.25),
    (2, 2.0),
])
def test__as_nullable_float(inp, expected):
    assert _as_nullable_float(inp) == expected


def test__normalize_meta_keywords_for_articles_field():
    f = _normalize_meta_keywords_for_articles_field
    assert f(None) == ""
    assert f("") == ""
    assert f("a, b,  c") == "a, b, c"
    assert f([" a ", "b", "", "c "]) == "a, b, c"


def test_store_article_insert_then_upsert_minimal():
    db = FakeConn()
    item = {
        "url": "https://www.elmostrador.cl/noticias/pais/2023/07/12/nota-3/?utm_source=x",
        "title": "T1",
        "body": "Contenido",
        "publication_date": "2023-07-12",
        "source": "elmostrador",
        "domain": "elmostrador.cl",
        "meta_keywords": ["k1", "k2"],
        "polarity": "0.1",
        "subjectivity": None,
        "language": "es",
    }

    # 1) insert
    art_id_1 = store_article(db, item)
    # 2) upsert mismo URL canónico → debe devolver el mismo id
    art_id_2 = store_article(db, item)

    assert art_id_1 == art_id_2

    # Confirmar que se usó la URL canónica (sin utm)
    can_url = "https://elmostrador.cl/noticias/pais/2023/07/12/nota-3"
    assert can_url in db.cur.articles_by_url
