# tests/unit/test_nlp_orchestrator_more_edges.py
import pytest
from scrapy_project.nlp_orchestrator import NLPOrchestrator

def test_ner_exception_safe():
    class BoomSpacy:
        def __call__(self, text):
            raise RuntimeError("spaCy NER crash")

    orch = NLPOrchestrator(
        spacy_model=BoomSpacy(),  # provocamos fallo en NER
        preprocessor=None,
        posverdad_nlp=None,
        framing_analyzer=None,
    )
    out = orch.process("texto cualquiera")
    assert "entities" in out and out["entities"] == []  # no rompe, fallback vacío
    # resto de claves mínimas presentes
    assert set(out.keys()) >= {"polarity", "subjectivity", "framing", "preprocessed", "sentiment"}

def test_sentiment_all_none():
    class NullSent:
        def analyze_sentiment(self, text):
            return None, None  # sin señal
        def subjectivity_proxy(self, doc_or_text):
            return None

    orch = NLPOrchestrator(
        spacy_model=None,
        preprocessor=None,
        posverdad_nlp=NullSent(),
        framing_analyzer=None,
    )
    out = orch.process("algún contenido no vacío")
    assert out["polarity"] is None
    assert out["subjectivity"] is None

def test_framing_ignored_empty_and_non_dict():
    class EmptyFraming:
        def analyze_framing(self, text):
            return {}  # dict vacío → ignorar

    class NonDictFraming:
        def analyze_framing(self, text):
            return "no-es-dict"  # tipo inválido → ignorar

    orch1 = NLPOrchestrator(spacy_model=None, preprocessor=None, posverdad_nlp=None, framing_analyzer=EmptyFraming())
    out1 = orch1.process("texto 1")
    assert out1.get("framing") in ({}, None)

    orch2 = NLPOrchestrator(spacy_model=None, preprocessor=None, posverdad_nlp=None, framing_analyzer=NonDictFraming())
    out2 = orch2.process("texto 2")
    assert out2.get("framing") in ({}, None)

def test_whitespace_early_return_safe():
    orch = NLPOrchestrator(spacy_model=None, preprocessor=None, posverdad_nlp=None, framing_analyzer=None)
    out = orch.process("   \n\t  ")  # solo blanco

    # Estructura mínima garantizada en early-return:
    required = {"entities", "preprocessed", "polarity", "subjectivity"}
    assert required.issubset(out.keys())

    # Valores seguros
    assert out["entities"] == []
    assert out["preprocessed"] == {}
    assert out["polarity"] is None
    assert out["subjectivity"] is None

    # Campos opcionales según implementación:
    # 'framing' puede estar ausente o ser dict vacío
    assert ("framing" not in out) or (out["framing"] in ({}, None))
    # 'sentiment' puede estar ausente en early-return
    assert ("sentiment" not in out) or (out["sentiment"] in ({}, None))

    # Otros campos (p.ej. 'topics') pueden existir: no los estrictamos.