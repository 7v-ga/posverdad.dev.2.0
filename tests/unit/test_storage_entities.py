from scrapy_project.storage_helpers import save_entities

class EntDB:
    def __init__(self):
        self.blocklisted = set()   # (lower(term), type)
        self.alias = {}            # (lower(alias), type) -> canonical_id
        self.entities = {}         # (name, type) -> id
        self.next_id = 1
        self.links = set()         # (article_id, entity_id)
        self._row = None

    def cursor(self): return self
    def commit(self): pass
    def rollback(self): pass
    def close(self): pass

    def execute(self, sql, params=None):
        low = sql.lower().strip()

        # blocklist check
        if "from entity_blocklist" in low and low.startswith("select 1"):
            name, typ = params
            self._row = (1,) if (name.lower(), typ) in self.blocklisted else None
            return

        # alias
        if "from entity_aliases" in low and low.startswith("select canonical_entity_id"):
            name, typ = params
            cid = self.alias.get((name.lower(), typ))
            self._row = (cid,) if cid else None
            return

        # get entity
        if low.startswith("select id from entities where name"):
            name, typ = params
            eid = self.entities.get((name, typ))
            self._row = (eid,) if eid else None
            return

        # create entity
        if low.startswith("insert into entities"):
            name, typ = params
            eid = self.entities.get((name, typ))
            if not eid:
                eid = self.next_id
                self.next_id += 1
                self.entities[(name, typ)] = eid
            self._row = (eid,)
            return

        # link
        if low.startswith("insert into articles_entities"):
            a_id, e_id = params
            self.links.add((a_id, e_id))
            return

        self._row = None

    def fetchone(self): return self._row


def test_save_entities_blocklist_skips_and_alias_links():
    db = EntDB()
    article_id = 9

    # Preparar blocklist y alias
    db.blocklisted.add(("bloqueado", "PERSON"))
    db.alias[("alias", "ORG")] = 42  # canonical preexistente

    ents = [
        {"text": "Bloqueado", "label": "PERSON"},   # debe saltarse
        {"text": "Alias", "label": "ORG"},          # debe linkear a 42
        {"text": "Nuevo", "label": "LOC"},          # debe crear entidad nueva y linkear
    ]

    save_entities(db, article_id, ents)

    # Debe contener vínculo a 42 y a la entidad creada "Nuevo"/LOC
    linked_ids = {eid for (_aid, eid) in db.links}
    assert 42 in linked_ids

    # Buscar id creado para ("Nuevo","LOC")
    created_id = db.entities.get(("Nuevo", "LOC"))
    assert created_id in linked_ids
