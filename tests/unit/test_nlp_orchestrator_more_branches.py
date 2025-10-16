import pytest
import logging
from unittest.mock import MagicMock
from scrapy_project.nlp_orchestrator import NLPOrchestrator

# ---- spaCy model string inválido → fallback a blank('es') (sin crashear) ----
def test_spacy_model_string_invalid_fallback_blank(monkeypatch):
    import scrapy_project.nlp_orchestrator as mod

    class FakeSpacyMod:
        def load(self, name): raise OSError("not found")
        def blank(self, lang): 
            # devolvemos un callable tipo nlp que produce un doc con .ents vacío
            return lambda text: type("Doc", (), {"ents": []})()

    fake_spacy = FakeSpacyMod()
    monkeypatch.setattr(mod, "spacy", fake_spacy, raising=False)

    o = NLPOrchestrator(spacy_model="modelo_inexistente", posverdad_nlp=None, framing_analyzer=None, preprocessor=None)
    out = o.analyze("hola")
    assert "entities" in out and isinstance(out["entities"], list)

# ---- _nlp no callable → salta NER sin romper ----
def test_non_callable_nlp_object_skips_ner():
    o = NLPOrchestrator(spacy_model=object(), posverdad_nlp=None, framing_analyzer=None, preprocessor=None)
    out = o.analyze("texto")
    assert out["entities"] == []  # no intentó llamar

# ---- Entidad con 'label' pero sin 'label_' → usa 'label' ----
class _EntLabelOnly:
    def __init__(self, text, label): self.text, self.label = text, label
class _Doc:
    def __init__(self, ents): self.ents = ents

def test_entity_uses_label_when_no_label_():
    def fake_nlp(t): return _Doc([_EntLabelOnly("Chile", "LOC")])
    o = NLPOrchestrator(spacy_model=fake_nlp, posverdad_nlp=None, framing_analyzer=None, preprocessor=None)
    out = o.analyze("Chile")
    assert {"text": "Chile", "label": "LOC"} in out["entities"]

# ---- Framing no-dict → ignorar; excepción → warning y dict vacío ----
def test_framing_non_dict_is_ignored():
    fr = MagicMock()
    fr.analyze_framing.return_value = ["no_dict"]
    o = NLPOrchestrator(spacy_model=None, posverdad_nlp=None, framing_analyzer=fr, preprocessor=None)
    out = o.analyze("t")
    assert out["framing"] == {}

def test_framing_exception_logs_warning(caplog):
    caplog.set_level(logging.WARNING)
    fr = MagicMock()
    fr.analyze_framing.side_effect = RuntimeError("boom")
    o = NLPOrchestrator(spacy_model=None, posverdad_nlp=None, framing_analyzer=fr, preprocessor=None)
    out = o.analyze("t")
    assert out["framing"] == {}
    assert any("framing analyzer falló" in rec.message for rec in caplog.records)

# ---- Preprocesador devuelve None/vacío → cae a texto original ----
def test_preprocessor_returns_none_or_empty_falls_back_to_original():
    pre = MagicMock()
    pre.preprocess.return_value = None
    o = NLPOrchestrator(spacy_model=None, posverdad_nlp=None, framing_analyzer=None, preprocessor=pre)
    out = o.analyze("ORIG")
    assert out["preprocessed"] == {}  # expuesto como vacío
    # y no crashea el resto del pipeline
