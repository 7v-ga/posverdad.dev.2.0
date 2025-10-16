# tests/unit/test_nlp_orchestrator_branches.py
import pytest
import warnings
from unittest.mock import MagicMock

from scrapy_project.nlp_orchestrator import run_nlp, NLPOrchestrator

# ---------- run_nlp: usa .analyze si existe; cae a .process con warning si no ----------
def test_run_nlp_prefers_analyze():
    class Orch:
        def analyze(self, text): return {"ok": True, "text": text}
        def process(self, text): return {"ok": False}
    out = run_nlp("hola", Orch())
    assert out["ok"] is True and out["text"] == "hola"

def test_run_nlp_falls_back_to_process_with_warning():
    class Orch:
        def process(self, text): return {"via": "process"}
    with pytest.warns(DeprecationWarning):
        out = run_nlp("x", Orch())
    assert out == {"via": "process"}

# ---------- early-return EXACTO para texto vacío ----------
def test_analyze_empty_text_matches_exact_structure():
    o = NLPOrchestrator(spacy_model=None, posverdad_nlp=None, framing_analyzer=None, preprocessor=None)
    out = o.analyze("   ")
    assert out == {
        "polarity": None,
        "subjectivity": None,
        "entities": [],
        "topics": [],
        "framing": {},
        "preprocessed": {},
    }  # estructura exacta (ver process…)  # :contentReference[oaicite:1]{index=1}

# ---------- preprocessor falla → warning, se sigue con texto original ----------
def test_preprocessor_raises_is_caught_and_skipped(monkeypatch):
    pre = MagicMock()
    pre.preprocess.side_effect = RuntimeError("boom")  # warning y continuar  # :contentReference[oaicite:2]{index=2}
    o = NLPOrchestrator(spacy_model=None, posverdad_nlp=None, framing_analyzer=None, preprocessor=pre)
    out = o.analyze("texto")
    assert out["preprocessed"] == {}
    assert out["entities"] == [] and out["framing"] == {} and out["polarity"] is None

# ---------- NER: éxito y excepción ----------
class _Ent:
    def __init__(self, text, label_): self.text, self.label_ = text, label_
class _Doc:
    def __init__(self, ents): self.ents = ents

def test_ner_happy_path_collects_entities():
    def fake_nlp(t): return _Doc([_Ent("Chile", "LOC"), _Ent("Boric", "PER")])
    o = NLPOrchestrator(spacy_model=fake_nlp, posverdad_nlp=None, framing_analyzer=None, preprocessor=None)
    out = o.analyze("Chile, Boric")
    assert {"text": "Chile", "label": "LOC"} in out["entities"] and {"text": "Boric", "label": "PER"} in out["entities"]  # :contentReference[oaicite:3]{index=3}

def test_ner_exception_is_caught_and_logged():
    def bad_nlp(t): raise ValueError("NER broke")  # warning y continuar  # :contentReference[oaicite:4]{index=4}
    o = NLPOrchestrator(spacy_model=bad_nlp, posverdad_nlp=None, framing_analyzer=None, preprocessor=None)
    out = o.analyze("x")
    assert out["entities"] == []

# ---------- Sentiment: formatos varios + excepción ----------
@pytest.mark.parametrize("sent,expected", [
    (1.0, 1.0),                          # numérico directo
    ("-1.0", -1.0),                      # string numérico
    ("POS", 1.0),                        # etiqueta directa
    (("NEG", {"POS": 0.2, "NEG": 0.8}), -0.6),  # tuple de (label, probs) → P(pos)-P(neg)
    ([("positive", 0.7), ("negative", 0.1)], 0.6),  # lista de pares
    ({"positive": 0.4, "negative": 0.6}, -0.2),     # mapping toplevel
    ({"label": "NEU"}, 0.0),             # label en dict
    ({"probs": {"pos": 0.9, "neg": 0.2}}, 0.7),     # contenedor probs  # :contentReference[oaicite:5]{index=5}
])
def test_sentiment_derives_polarity_from_multiple_formats(sent, expected):
    pv = MagicMock()
    pv.analyze_sentiment.return_value = sent
    o = NLPOrchestrator(spacy_model=None, posverdad_nlp=pv, framing_analyzer=None, preprocessor=None)
    out = o.analyze("texto")
    assert out["sentiment"] == sent
    assert pytest.approx(out["polarity"], rel=1e-6) == expected  # via _derive_polarity_from_sentiment  # :contentReference[oaicite:6]{index=6}

def test_sentiment_exception_is_caught():
    pv = MagicMock()
    pv.analyze_sentiment.side_effect = RuntimeError("predict fail")  # warning  # :contentReference[oaicite:7]{index=7}
    o = NLPOrchestrator(spacy_model=None, posverdad_nlp=pv, framing_analyzer=None, preprocessor=None)
    out = o.analyze("x")
    assert out["polarity"] is None and out["sentiment"] is None

# ---------- Subjectivity: string numérico → _to_float ----------
def test_subjectivity_string_numeric_is_converted():
    pv = MagicMock()
    pv.analyze_sentiment.return_value = None
    pv.subjectivity_proxy.return_value = "0.42"   # conv. numérica  # :contentReference[oaicite:8]{index=8}
    o = NLPOrchestrator(spacy_model=None, posverdad_nlp=pv, framing_analyzer=None, preprocessor=None)
    out = o.analyze("texto")
    assert out["subjectivity"] == pytest.approx(0.42, rel=1e-6)

# ---------- Framing: prefer analyze_framing, descarta dict vacío, captura excepciones ----------
def test_framing_prefers_analyze_framing_and_accepts_non_empty_dict():
    fr = MagicMock()
    fr.analyze_framing.return_value = {"ideological_frame": "x"}  # prioridad sobre analyze  # :contentReference[oaicite:9]{index=9}
    fr.analyze.return_value = {"ideological_frame": "y"}
    o = NLPOrchestrator(spacy_model=None, posverdad_nlp=None, framing_analyzer=fr, preprocessor=None)
    out = o.analyze("texto")
    assert out["framing"] == {"ideological_frame": "x"}

def test_framing_ignores_empty_dict_and_catches_exception():
    fr = MagicMock()
    fr.analyze_framing.return_value = {}          # dict vacío → ignorar
    o = NLPOrchestrator(spacy_model=None, posverdad_nlp=None, framing_analyzer=fr, preprocessor=None)
    out = o.analyze("texto")
    assert out["framing"] == {}

    fr2 = MagicMock()
    fr2.analyze_framing.side_effect = RuntimeError("framing boom")  # warning ruta excepción  # :contentReference[oaicite:10]{index=10}
    o2 = NLPOrchestrator(spacy_model=None, posverdad_nlp=None, framing_analyzer=fr2, preprocessor=None)
    out2 = o2.analyze("texto")
    assert out2["framing"] == {}

def test_preprocessor_dict_with_text_is_used_downstream():
    # preprocessor devuelve dict con 'text' -> ese texto se usa para NER/sentiment/framing
    called = {"nlp": None, "sent": None, "subj": None, "fr": None}

    pre = MagicMock()
    pre.preprocess.return_value = {"text": "LIMPIO", "tokens": ["li", "mpio"]}

    def fake_nlp(t):
        called["nlp"] = t
        return _Doc([_Ent("Chile", "LOC")])  # devolver una entidad sencilla

    pv = MagicMock()
    pv.analyze_sentiment.side_effect = lambda t: called.__setitem__("sent", t) or {"positive": 0.8, "negative": 0.1}
    pv.subjectivity_proxy.side_effect = lambda t: called.__setitem__("subj", t) or "0.33"

    fr = MagicMock()
    fr.analyze_framing.side_effect = lambda t: called.__setitem__("fr", t) or {"ideological_frame": "x"}

    o = NLPOrchestrator(spacy_model=fake_nlp, posverdad_nlp=pv, framing_analyzer=fr, preprocessor=pre)
    out = o.analyze("texto original")

    # Se usó "LIMPIO" en todas las etapas downstream
    assert called["nlp"] == "LIMPIO"
    assert called["sent"] == "LIMPIO"
    assert called["subj"] == "LIMPIO"
    assert called["fr"] == "LIMPIO"

    # Y el preprocesado aparece expuesto
    assert out["preprocessed"] == {"text": "LIMPIO", "tokens": ["li", "mpio"]}
    # Señales llenas coherentes
    assert isinstance(out["entities"], list) and {"text": "Chile", "label": "LOC"} in out["entities"]
    assert out["polarity"] == pytest.approx(0.7, rel=1e-6)  # 0.8 - 0.1
    assert out["subjectivity"] == pytest.approx(0.33, rel=1e-6)
    assert out["framing"] == {"ideological_frame": "x"}


def test_preprocessor_dict_without_text_falls_back_to_original_text():
    called = {"nlp": None, "sent": None, "subj": None, "fr": None}

    pre = MagicMock()
    pre.preprocess.return_value = {"tokens": ["no", "text"], "lemmas": []}  # sin 'text'

    def fake_nlp(t):
        called["nlp"] = t
        return _Doc([])

    pv = MagicMock()
    pv.analyze_sentiment.side_effect = lambda t: called.__setitem__("sent", t) or "NEU"
    pv.subjectivity_proxy.side_effect = lambda t: called.__setitem__("subj", t) or "0"

    fr = MagicMock()
    fr.analyze_framing.side_effect = lambda t: called.__setitem__("fr", t) or {}

    o = NLPOrchestrator(spacy_model=fake_nlp, posverdad_nlp=pv, framing_analyzer=fr, preprocessor=pre)
    out = o.analyze("texto ORIG")

    # Como no hubo 'text' en el dict, se usa el original
    assert called["nlp"] == "texto ORIG"
    assert called["sent"] == "texto ORIG"
    assert called["subj"] == "texto ORIG"
    assert called["fr"] == "texto ORIG"

    # El preprocesado igual queda expuesto tal cual llegó
    assert out["preprocessed"] == {"tokens": ["no", "text"], "lemmas": []}
    # Y como framing devolvió {}, se ignora
    assert out["framing"] == {}
