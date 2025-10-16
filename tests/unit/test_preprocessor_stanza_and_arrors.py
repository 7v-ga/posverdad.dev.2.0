import types
import pytest
import importlib
import scrapy_project.preprocessor as prep

pytestmark = pytest.mark.unit

def test_invalid_engine_raises_value_error():
    with pytest.raises(ValueError):
        prep.Preprocessor(engine="otra-cosa")

def test_stanza_path_with_fake_module(monkeypatch):
    # Fake stanza module (no requiere instalar nada)
    fake_stanza = types.SimpleNamespace()
    calls = {"download": [], "pipeline": 0}

    def _download(lang, verbose=False): calls["download"].append((lang, verbose))

    class _W:
        def __init__(self, text, lemma, upos): self.text, self.lemma, self.upos = text, lemma, upos
    class _S:
        def __init__(self, words): self.words = words
    class _Doc:
        def __init__(self, sentences): self.sentences = sentences

    class _Pipeline:
        def __init__(self, lang, processors=None, verbose=False): calls["pipeline"] += 1
        def __call__(self, text):
            # incluye puntuación que el código filtra
            words = [
                _W("Hola", "hola", "INTJ"),
                _W(",", ",", "PUNCT"),
                _W("Chile", "Chile", "PROPN"),
                _W(".", ".", "PUNCT"),
            ]
            return _Doc([_S(words)])

    fake_stanza.download = _download
    fake_stanza.Pipeline = _Pipeline

    # Parches dentro del módulo ya importado
    monkeypatch.setattr(prep, "stanza_available", True, raising=False)
    monkeypatch.setattr(prep, "stanza", fake_stanza, raising=False)

    p = prep.Preprocessor(engine="stanza")
    out = p.preprocess("Hola, Chile.")
    assert out["engine"] == "stanza"
    assert out["tokens"] == ["Hola", "Chile"]
    assert out["lemmas"] == ["hola", "Chile"]
    assert out["pos"] == ["INTJ", "PROPN"]
    assert calls["download"] and calls["pipeline"] == 1
