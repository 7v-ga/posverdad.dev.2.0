
import pytest
from scrapy_project.preprocessor import Preprocessor

@pytest.fixture
def preprocessor():
    return Preprocessor()

def test_preprocess_normal_text(preprocessor):
    text = "Esto es una prueba de procesamiento de texto."
    result = preprocessor.preprocess(text)
    assert result is not None
    assert "tokens" in result
    assert isinstance(result["tokens"], list)
    assert any("prueba" in t.lower() for t in result["tokens"])

def test_preprocess_empty_string(preprocessor):
    result = preprocessor.preprocess("")
    assert result is not None
    assert "tokens" in result
    assert result["tokens"] == []

def test_preprocess_html(preprocessor):
    html_text = "<p>Hola mundo</p>"
    result = preprocessor.preprocess(html_text)
    assert result is not None
    assert "tokens" in result
    assert any("hola" in t.lower() for t in result["tokens"])

def test_preprocess_stopwords_only(preprocessor):
    text = "el la los las"
    result = preprocessor.preprocess(text)
    assert result is not None
    assert result["tokens"] == []

def test_preprocess_none_input(preprocessor):
    with pytest.raises(TypeError):
        preprocessor.preprocess(None)
