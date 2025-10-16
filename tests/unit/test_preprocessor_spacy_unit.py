from scrapy_project.preprocessor import Preprocessor

class FakeToken:
    def __init__(self, text, lemma_, pos_, is_stop=False, is_punct=False):
        self.text = text
        self.lemma_ = lemma_
        self.pos_ = pos_
        self.is_stop = is_stop
        self.is_punct = is_punct

class FakeSpacy:
    def __call__(self, text):
        # "Hola, muy bonito." -> filtra stop/punct -> ["Hola", "bonito"]
        return [
            FakeToken("Hola", "hola", "NOUN", is_stop=False, is_punct=False),
            FakeToken(",", ",", "PUNCT", is_stop=False, is_punct=True),
            FakeToken("muy", "muy", "ADV", is_stop=True, is_punct=False),
            FakeToken("bonito", "bonito", "ADJ", is_stop=False, is_punct=False),
            FakeToken(".", ".", "PUNCT", is_stop=False, is_punct=True),
        ]

def test_preprocess_empty_text_returns_structure(mocker):
    # Evitar carga real de spaCy en __init__
    mocker.patch("scrapy_project.preprocessor.spacy.load", return_value=FakeSpacy())
    p = Preprocessor(engine="spacy")
    out = p.preprocess("   ")
    assert out == {"engine": "spacy", "tokens": [], "lemmas": [], "pos": []}

def test_preprocess_spacy_filters_stop_and_punct(mocker):
    mocker.patch("scrapy_project.preprocessor.spacy.load", return_value=FakeSpacy())
    p = Preprocessor(engine="spacy")
    out = p.preprocess("Hola, muy bonito.")
    assert out["engine"] == "spacy"
    assert out["tokens"] == ["Hola", "bonito"]
    assert out["lemmas"] == ["hola", "bonito"]
    assert out["pos"] == ["NOUN", "ADJ"]

def test_preprocess_raises_on_none(mocker):
    mocker.patch("scrapy_project.preprocessor.spacy.load", return_value=FakeSpacy())
    p = Preprocessor(engine="spacy")
    import pytest
    with pytest.raises(TypeError):
        p.preprocess(None)

def test_preprocessor_invalid_engine():
    import pytest
    with pytest.raises(ValueError):
        Preprocessor(engine="otro")
