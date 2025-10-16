# tests/unit/test_nlp_orchestrator_formats_extra.py
import pytest
from scrapy_project import nlp_orchestrator as no

def test_mapping_pos_neg_delta():
    v = no._pos_neg_from_mapping({"positive": "0.70", "negative": 0.2})
    assert v == pytest.approx(0.5)

def test_tuple_prefers_probs_over_label():
    # Fallback prioriza dict de probabilidades sobre la etiqueta
    v = no._derive_polarity_from_tuple(("POS", {"NEG": 0.25, "POS": 0.55}))
    assert v == pytest.approx(0.30)

def test_list_of_pairs_to_delta():
    v = no._derive_polarity_from_tuple([("NEG", 0.3), ("POS", "0.6")])
    assert v == pytest.approx(0.3)

def test_label_and_numeric_str():
    assert no._derive_polarity_from_sentiment("neutral") == 0.0
    assert no._derive_polarity_from_sentiment(" -0.4 ") == pytest.approx(-0.4)
