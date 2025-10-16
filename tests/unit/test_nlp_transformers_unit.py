from scrapy_project.nlp_transformers import PostverdadNLP

class FakeAnalyzer:
    def predict(self, text):
        class R:
            output = "POS"
            probas = {"POS": 0.9, "NEG": 0.05, "NEU": 0.05}
        return R()

class FakeToken:
    def __init__(self, pos_, dep_):
        self.pos_ = pos_
        self.dep_ = dep_

class FakeSpacyDoc(list):
    pass

class FakeSpacy:
    def __call__(self, text):
        # 4 tokens, 2 cumplen criterio (ADJ/VERB y dep en conjunto)
        doc = FakeSpacyDoc([
            FakeToken("ADJ", "amod"),   # cuenta
            FakeToken("VERB", "advcl"), # cuenta
            FakeToken("NOUN", "nsubj"),
            FakeToken("ADP", "case"),
        ])
        return doc

def test_analyze_sentiment_returns_none_when_no_analyzer():
    nlp = PostverdadNLP(nlp_model=None)
    # Forzamos que el analyzer sea None
    nlp.sa = None
    assert nlp.analyze_sentiment("texto") == (None, None)

def test_analyze_sentiment_ok():
    nlp = PostverdadNLP(nlp_model=None)
    nlp.sa = FakeAnalyzer()
    pol, score = nlp.analyze_sentiment("buen día")
    assert pol == 1.0 and 0.0 <= score <= 1.0

def test_subjectivity_proxy_none_when_no_spacy_or_blank():
    nlp = PostverdadNLP(nlp_model=None)
    assert nlp.subjectivity_proxy("   ") is None
    assert nlp.subjectivity_proxy("texto") is None  # no hay spacy

def test_subjectivity_proxy_ok():
    nlp = PostverdadNLP(nlp_model=FakeSpacy())
    val = nlp.subjectivity_proxy("algo de texto")
    # 2/4 = 0.5
    assert val == 0.5
