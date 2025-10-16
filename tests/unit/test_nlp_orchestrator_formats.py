# tests/unit/test_nlp_orchestrator_formats.py
import pytest

from scrapy_project.nlp_orchestrator import NLPOrchestrator, run_nlp


# -----------------------------
# Fakes utilitarias
# -----------------------------
class FakeEnt:
    def __init__(self, text, label):
        self.text = text
        self.label_ = label


class FakeDoc:
    def __init__(self, ents):
        self.ents = ents


class FakeSpacyOK:
    """Modelo spaCy fake que devuelve 2 entidades."""
    def __call__(self, text):
        return FakeDoc([FakeEnt("Chile", "LOC"), FakeEnt("Gabriel", "PER")])


class FakeSpacyBoom:
    """Modelo spaCy fake que lanza excepción al ser invocado."""
    def __call__(self, text):
        raise RuntimeError("spaCy pipeline crashed")


class FakePreprocDict:
    """Preprocesador que devuelve un dict (el test espera que se preserve en out['preprocessed'])."""
    def preprocess(self, text):
        return {"text": "hola mundo", "tokens": ["hola", "mundo"]}


class FakePreprocStr:
    """Preprocesador que devuelve un string normalizado."""
    def preprocess(self, text):
        return "texto_limpio"


class FakePreprocBoom:
    """Preprocesador que lanza excepción para cubrir rama de warning."""
    def preprocess(self, text):
        raise ValueError("preproc fail")


class FakeFramingAnalyze:
    def analyze(self, text):
        return {"frame": "X"}


class FakeFramingAnalyzeFraming:
    def analyze_framing(self, text):
        return {"frame": "Y"}


class FakeFramingBoom:
    def analyze(self, text):
        raise RuntimeError("framing fail")


# Sentiment fakes diversos
class FakeSentimentLabelObj:
    def __init__(self, label):
        self.label_ = label  # objeto con atributo label_


class FakeSentimentProbsObj:
    def __init__(self, probs):
        self.probs = probs  # objeto con atributo probs=dict


# Orquestador “legacy” para probar run_nlp -> process + DeprecationWarning
class LegacyOnlyProcess:
    def process(self, text):
        return {"legacy": True, "text": text}


# -----------------------------
# Tests
# -----------------------------

@pytest.mark.unit
def test_empty_text_returns_exact_contract():
    """Early-return: texto vacío/espacios debe devolver estructura exacta (igual que el test 'conocido')."""
    orch = NLPOrchestrator(
        spacy_model=FakeSpacyOK(),
        postverdad_nlp=None,
        framing_analyzer=None,
        preprocessor=None,
    )
    out = orch.analyze("   ")
    assert out == {
        "polarity": None,
        "subjectivity": None,
        "entities": [],
        "topics": [],
        "framing": {},
        "preprocessed": {},
    }


@pytest.mark.unit
def test_preprocessor_dict_is_preserved_and_used_for_ner_sentiment_subjectivity_framing():
    """Si el preprocesador devuelve dict, se preserva en out['preprocessed'], y 'text' se usa como entrada."""
    class FakePVNLP:
        def analyze_sentiment(self, text):  # tuple: (polarity, confidence)
            return (1.0, 0.88)
        def subjectivity_proxy(self, text):
            return "0.6"

    orch = NLPOrchestrator(
        spacy_model=FakeSpacyOK(),
        postverdad_nlp=FakePVNLP(),
        framing_analyzer=FakeFramingAnalyze(),
        preprocessor=FakePreprocDict(),
    )
    out = orch.analyze("cualquier cosa")
    # preprocessed dict
    assert isinstance(out.get("preprocessed"), dict) and out["preprocessed"].get("tokens") == ["hola", "mundo"]
    # NER
    assert out["entities"] and {"text": "Chile", "label": "LOC"} in out["entities"]
    # Sentiment -> polarity derivada desde tupla
    assert out["polarity"] == 1.0
    # Subjectivity numérica (string -> float)
    assert out["subjectivity"] == 0.6
    # Framing
    assert out["framing"] == {"frame": "X"}


@pytest.mark.unit
def test_preprocessor_str_normalizes_text_path_and_spacy_ner_ok():
    class FakePVNLP:
        def analyze_sentiment(self, text):
            return {"label": "positive"}  # dict con label -> +1.0
        def subjectivity_proxy(self, text):
            return 0.1

    orch = NLPOrchestrator(
        spacy_model=FakeSpacyOK(),
        postverdad_nlp=FakePVNLP(),
        framing_analyzer=FakeFramingAnalyzeFraming(),
        preprocessor=FakePreprocStr(),
    )
    out = orch.analyze("Texto con ruido")
    assert out["polarity"] == 1.0
    assert out["framing"] == {"frame": "Y"}
    assert out["entities"]  # hay entidades


@pytest.mark.unit
def test_preprocessor_raises_and_spacy_raises_paths_are_safe():
    class FakePVNLP:
        def analyze_sentiment(self, text):
            return {"probs": {"POS": 0.7, "NEG": 0.2}}  # -> 0.5
        def subjectivity_proxy(self, text):
            raise RuntimeError("subj fail")

    orch = NLPOrchestrator(
        spacy_model=FakeSpacyBoom(),       # NER lanza excepción
        postverdad_nlp=FakePVNLP(),
        framing_analyzer=FakeFramingBoom(),  # framing lanza excepción
        preprocessor=FakePreprocBoom(),    # preproc lanza excepción
    )
    out = orch.analyze("Texto")
    # Aún así, debe poblar polarity y NO reventar
    assert out["polarity"] == pytest.approx(0.5, rel=1e-6)
    # Subjectivity no seteada por error
    assert out["subjectivity"] is None
    # NER vacío por crash (el orquestador usa lista vacía)
    assert out["entities"] == []
    # NOTA: según la implementación, cuando no hay entidades se queda como dict vacío o lista;
    # ajusta aserción si tu implementación usa lista vacía:
    # assert out["entities"] == []


# -----------------------------
# Paramétricas de sentimiento
# -----------------------------
@pytest.mark.unit
@pytest.mark.parametrize(
    "sent, expected",
    [
        (0.75, 0.75),                 # numérico
        ("-0.3", -0.3),               # string numérico
        ("POS", 1.0),                 # etiqueta positiva
        ("NEG", -1.0),                # etiqueta negativa
        ("NEU", 0.0),                 # etiqueta neutra
        ((1.0, 0.9), 1.0),            # tupla (polarity, extra)
        ({"polarity": 0.2}, 0.2),     # dict polarity
        ({"score": -0.4}, -0.4),      # dict score
        ({"label": "positive"}, 1.0), # dict label
        ({"probs": {"positive": 0.9, "negative": 0.1}}, 0.8),  # P(pos)-P(neg)
        ({"POS": 0.6, "NEG": 0.1}, 0.5),                       # mapping toplevel
        (FakeSentimentLabelObj("NEG"), -1.0),                  # objeto con label_
        (FakeSentimentProbsObj({"POS": 0.3, "NEG": 0.2}), 0.1) # objeto con probs
    ],
)
def test_sentiment_derivation_various_formats(sent, expected):
    class PV:
        def analyze_sentiment(self, text):
            return sent
        def subjectivity_proxy(self, text):
            return None

    orch = NLPOrchestrator(
        spacy_model=None,  # sin NER
        postverdad_nlp=PV(),
        framing_analyzer=None,
        preprocessor=None,
    )
    out = orch.analyze("algo")
    assert out["polarity"] == pytest.approx(expected, rel=1e-6)


@pytest.mark.unit
def test_run_nlp_adapter_emits_deprecation_when_only_process():
    with pytest.warns(DeprecationWarning):
        result = run_nlp("texto", LegacyOnlyProcess())
    assert result == {"legacy": True, "text": "texto"}


@pytest.mark.unit
def test_subjectivity_and_framing_paths_with_normal_values():
    class PV:
        def analyze_sentiment(self, text):
            return "NEU"  # 0.0
        def subjectivity_proxy(self, text):
            return "0.42"

    orch = NLPOrchestrator(
        spacy_model=FakeSpacyOK(),
        postverdad_nlp=PV(),
        framing_analyzer=FakeFramingAnalyze(),
        preprocessor=None,
    )
    out = orch.analyze("texto")
    assert out["polarity"] == 0.0
    assert out["subjectivity"] == 0.42
    assert out["framing"] == {"frame": "X"}
    assert {"text": "Chile", "label": "LOC"} in out["entities"]
