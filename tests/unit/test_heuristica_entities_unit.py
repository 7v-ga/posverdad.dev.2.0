# tests/unit/test_heuristica_entities_unit.py
import pytest
from scrapy_project.heuristica_entities import clean_and_unify_entities

pytestmark = pytest.mark.unit


# --- Fakes de spaCy para probar el filtro POS (BAD_POS) ---
class _FakeTok:
    def __init__(self, text, pos_):
        self.text = text
        self.pos_ = pos_

class _FakeDoc(list):
    """Soporta iteración como si fuera un Doc de spaCy."""


def test_stop_ents_and_blanks_filtered():
    # Incluye stop-ents ("además", "ayer"), texto vacío y de 1 char → deben descartarse
    ents = [
        {"text": "además", "label": "LOC"},
        {"text": "ayer", "label": "PER"},
        {"text": "", "label": "PER"},
        {"text": " ", "label": "ORG"},
        {"text": "x", "label": "MISC"},
        {"text": "Chile", "label": "LOC"},
    ]
    out = clean_and_unify_entities(ents, spacy_doc=None)
    assert out == [{"text": "Chile", "label": "LOC"}]


def test_pos_filter_discards_when_all_bad_pos():
    # Si TODOS los tokens con ese texto son de BAD_POS (ADV/SCONJ/CCONJ/DET/PRON), se descarta
    # Montamos un doc con varias ocurrencias de la misma "entidad" en BAD_POS
    doc = _FakeDoc([
        _FakeTok("Sin", "SCONJ"),
        _FakeTok("embargo", "NOUN"),
        _FakeTok("Sin embargo", "ADV"),  # no matchea texto exacto, probamos "Hoy" y "Tambien"
        _FakeTok("Hoy", "ADV"),
        _FakeTok("Tambien", "ADV"),  # deliberately not stoplist, pero BAD_POS
        _FakeTok("Chile", "PROPN"),
    ])
    ents = [
        {"text": "Hoy", "label": "MISC"},        # BAD_POS → descarta
        {"text": "Tambien", "label": "MISC"},    # BAD_POS → descarta
        {"text": "Chile", "label": "LOC"},       # PROPN → queda
    ]
    out = clean_and_unify_entities(ents, spacy_doc=doc)
    assert out == [{"text": "Chile", "label": "LOC"}]


def test_unify_lastname_to_fullname_unique():
    # Un único candidato: "Pérez" → "Juan Pérez"
    ents = [
        {"text": "Juan Pérez", "label": "PER"},
        {"text": "Pérez", "label": "PER"},
        {"text": "Chile", "label": "LOC"},
    ]
    out = clean_and_unify_entities(ents, spacy_doc=None)
    # "Pérez" debe mapear al nombre completo y deduplicarse
    assert {"text": "Juan Pérez", "label": "PER"} in out
    # no debe existir la forma corta
    assert not any(e["text"] == "Pérez" and e["label"] == "PER" for e in out)
    # otras entidades quedan
    assert {"text": "Chile", "label": "LOC"} in out


def test_unify_lastname_ambiguous_does_not_change():
    # Dos candidatos distintos con el mismo apellido → NO unifica
    ents = [
        {"text": "Juan Pérez", "label": "PER"},
        {"text": "María Pérez", "label": "PER"},
        {"text": "Pérez", "label": "PER"},
    ]
    out = clean_and_unify_entities(ents, spacy_doc=None)
    # Debe permanecer "Pérez" tal cual (sin reemplazo por nombre completo)
    assert {"text": "Pérez", "label": "PER"} in out
    assert {"text": "Juan Pérez", "label": "PER"} in out
    assert {"text": "María Pérez", "label": "PER"} in out


def test_deduplicate_and_label_preservation():
    # Deduplicación por (texto,label) exacto, pero permite mismo texto con distinto label
    ents = [
        {"text": "Chile", "label": "LOC"},
        {"text": "Chile", "label": "LOC"},   # duplicado exacto
        {"text": "Chile", "label": "ORG"},   # mismo texto, distinto label → válido
        {"text": "Boric", "label": "PER"},
        {"text": "Boric", "label": "PER"},   # duplicado exacto
    ]
    out = clean_and_unify_entities(ents, spacy_doc=None)
    assert out.count({"text": "Chile", "label": "LOC"}) == 1
    assert {"text": "Chile", "label": "ORG"} in out
    assert out.count({"text": "Boric", "label": "PER"}) == 1
    
def test_unicode_and_case_stoplist():
    # "Además" (con tilde, mayúscula) debe ser filtrada por stoplist (comparación en lower)
    ents = [
        {"text": "Además", "label": "MISC"},
        {"text": "Ñuñoa", "label": "LOC"},
    ]
    out = clean_and_unify_entities(ents, spacy_doc=None)
    assert out == [{"text": "Ñuñoa", "label": "LOC"}]


def test_pos_filter_keeps_if_any_good_pos():
    # Si hay al menos un token no-BAD_POS para el mismo texto, no se descarta
    doc = _FakeDoc([
        _FakeTok("Tambien", "ADV"),   # BAD_POS
        _FakeTok("Tambien", "PROPN"), # POS "bueno" (no está en BAD_POS)
    ])
    ents = [{"text": "Tambien", "label": "MISC"}]
    out = clean_and_unify_entities(ents, spacy_doc=doc)
    assert out == [{"text": "Tambien", "label": "MISC"}]
