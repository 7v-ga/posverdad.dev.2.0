import pytest
from unittest.mock import Mock
from scrapy_project.nlp_transformers import PostverdadNLP

pytestmark = pytest.mark.unit

class _FakeResult:
    def __init__(self, output, probas):
        self.output = output
        self.probas = probas

def test_analyze_sentiment_unknown_label_defaults_zero(monkeypatch):
    nlp = PostverdadNLP(nlp_model=None)
    nlp.sa = Mock()
    nlp.sa.predict.return_value = _FakeResult("???", {"POS": 0.99})
    pol, score = nlp.analyze_sentiment("texto")
    assert pol == 0.0 and score == 0.0

def test_analyze_sentiment_predict_exception(monkeypatch):
    nlp = PostverdadNLP(nlp_model=None)
    nlp.sa = Mock()
    nlp.sa.predict.side_effect = RuntimeError("boom")
    pol, score = nlp.analyze_sentiment("texto")
    assert pol is None and score is None

def test_subjectivity_proxy_spacy_throws(monkeypatch):
    fake_spacy = Mock(side_effect=RuntimeError("spaCy fail"))
    nlp = PostverdadNLP(nlp_model=fake_spacy)
    assert nlp.subjectivity_proxy("texto") is None
