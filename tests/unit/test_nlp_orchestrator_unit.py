from scrapy_project.nlp_orchestrator import NLPOrchestrator

class FakeSpacy:
    def __call__(self, text):
        class Ent: 
            def __init__(self, t, l): self.text, self.label_ = t, l
        class Doc:
            ents = [Ent("Chile", "LOC"), Ent("Boric", "PER")]
        return Doc()

class FakePVNLP:
    def analyze_sentiment(self, text):
        return (1.0, 0.88)
    def subjectivity_proxy(self, text):
        return 0.25

class FakeLLM:
    def analyze_framing(self, text):
        return {"ideological_frame": "progresista", "narrative_role": {"actor":["X"],"victim":[],"antagonist":[]}, "emotions":["esperanza"], "summary":"..."}
    
class FakePreproc:
    def preprocess(self, text):
        return {"engine":"spacy","tokens":["hola"],"lemmas":["hola"],"pos":["INTJ"]}

def test_analyze_full_ok():
    orch = NLPOrchestrator(
        spacy_model=FakeSpacy(),
        postverdad_nlp=FakePVNLP(),
        framing_analyzer=FakeLLM(),
        preprocessor=FakePreproc(),
    )
    out = orch.analyze("Texto de prueba")
    assert out["polarity"] == 1.0
    assert out["subjectivity"] == 0.25
    assert len(out["entities"]) == 2
    assert out["framing"]["ideological_frame"] == "progresista"
    assert out["preprocessed"]["tokens"] == ["hola"]

def test_analyze_empty_text_returns_defaults():
    orch = NLPOrchestrator(
        spacy_model=FakeSpacy(),
        postverdad_nlp=FakePVNLP(),
        framing_analyzer=FakeLLM(),
        preprocessor=FakePreproc(),
    )
    out = orch.analyze("   ")
    assert out == {
        "polarity": None, "subjectivity": None, "entities": [],
        "topics": [], "framing": {}, "preprocessed": {}
    }

def test_analyze_handles_internal_exceptions(mocker):
    # Forzamos excepciones en cada bloque para cubrir excepts
    bad_spacy = mocker.Mock(side_effect=RuntimeError("spaCy fail"))
    bad_pv = mocker.Mock()
    bad_pv.analyze_sentiment.side_effect = Exception("sa fail")
    bad_pv.subjectivity_proxy.side_effect = Exception("subj fail")
    bad_llm = mocker.Mock()
    bad_llm.analyze_framing.side_effect = Exception("llm fail")
    bad_pre = mocker.Mock()
    bad_pre.preprocess.side_effect = Exception("pre fail")

    orch = NLPOrchestrator(
        spacy_model=bad_spacy,
        postverdad_nlp=bad_pv,
        framing_analyzer=bad_llm,
        preprocessor=bad_pre,
    )
    out = orch.analyze("texto")
    # A pesar de los errores, retorna estructura por defecto para esos campos
    assert out["polarity"] is None
    assert out["subjectivity"] is None
    assert out["entities"] == []
    assert out["framing"] == {}
    assert out["preprocessed"] == {}
