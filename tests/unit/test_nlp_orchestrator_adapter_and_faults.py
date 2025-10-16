# tests/unit/test_nlp_orchestrator_adapter_and_faults.py
import pytest
from scrapy_project.nlp_orchestrator import run_nlp, NLPOrchestrator

def test_adapter_prefers_analyze():
    class Ok:
        def analyze(self, t): return {"ok": True}
    assert run_nlp("x", Ok()) == {"ok": True}

def test_adapter_process_deprecated_warning():
    class Old:
        def process(self, t): return {"legacy": True}
    with pytest.warns(DeprecationWarning):
        assert run_nlp("x", Old()) == {"legacy": True}

def test_orchestrator_preprocessor_fault_tolerant(caplog):
    class BoomPre:
        def preprocess(self, t): raise TypeError("bad pre")
    orch = NLPOrchestrator(
        preprocessor=BoomPre(),
        spacy_model=None, posverdad_nlp=None, framing_analyzer=None
    )
    out = orch.process("texto cualquiera")
    # No rompe y devuelve estructura segura
    assert set(out.keys()) >= {
        "entities", "framing", "preprocessed", "sentiment", "polarity", "subjectivity"
    }
    assert out["preprocessed"] == {}

def test_orchestrator_uses_analyze_framing_when_available():
    class DummyFraming:
        # Solo define analyze_framing (no .analyze)
        def analyze_framing(self, text):
            # Debe ser dict NO vacío para que el orquestador lo acepte
            return {
                "ideological_frame": "centro",
                "narrative_role": {"actor": ["Gobierno"], "victim": [], "antagonist": []},
                "emotions": ["preocupación"],
                "summary": "El artículo encuadra el tema desde un punto de vista moderado."
            }

    from scrapy_project.nlp_orchestrator import NLPOrchestrator
    orch = NLPOrchestrator(
        spacy_model=None, posverdad_nlp=None,
        preprocessor=None, framing_analyzer=DummyFraming()
    )
    out = orch.process("texto cualquiera")
    assert isinstance(out.get("framing"), dict) and out["framing"]
    assert out["framing"]["ideological_frame"] == "centro"
