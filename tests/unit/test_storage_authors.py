from scrapy_project.storage_helpers import save_authors

class AuthorsDB:
    """Fake DB con tablas in-memory y reglas mínimas para autores."""
    def __init__(self):
        self.authors = {}           # name -> id
        self.next_author_id = 1
        self.articles_authors = set()  # (article_id, author_id)
        self.calls = []

    def cursor(self):
        return self

    # API tipo cursor
    def execute(self, sql, params=None):
        self.calls.append((sql.strip(), params))
        low = sql.lower().strip()

        if low.startswith("insert into authors"):
            name = params[0]
            if name not in self.authors:
                self.authors[name] = self.next_author_id
                self.next_author_id += 1
            return

        if low.startswith("select id from authors where name"):
            name = params[0]
            rid = self.authors.get(name)
            self._row = (rid,) if rid else None
            return

        if low.startswith("insert into articles_authors"):
            a_id, au_id = params
            self.articles_authors.add((a_id, au_id))
            return

        # RETURNING id
        if "returning id" in low and low.startswith("insert into authors"):
            # ya manejado arriba; preparar fetchone
            name = params[0]
            self._row = (self.authors[name],)
            return

        self._row = None

    def fetchone(self):
        return getattr(self, "_row", None)

    def commit(self):
        pass

    def rollback(self):
        pass

    def close(self):
        pass


def test_save_authors_split_and_dedup_string_and_list():
    db = AuthorsDB()
    article_id = 77

    # Caso 1: string "A, B"
    save_authors(db, article_id, "A, B")
    assert db.authors == {"A": 1, "B": 2}
    assert db.articles_authors == {(77, 1), (77, 2)}

    # Caso 2: lista que mezcla "A, B" y "C", y duplica "A"
    save_authors(db, article_id, ["A, B", "C", "A"])
    # No deben duplicarse autores ni relaciones
    assert db.authors == {"A": 1, "B": 2, "C": 3}
    assert db.articles_authors == {(77, 1), (77, 2), (77, 3)}

