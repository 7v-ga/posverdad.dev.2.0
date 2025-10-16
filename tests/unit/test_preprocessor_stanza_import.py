# tests/unit/test_preprocessor_stanza_import.py
import pytest
import scrapy_project.preprocessor as pp

def test_preprocessor_stanza_importerror(monkeypatch):
    # forzamos el flag para simular que Stanza no está disponible
    monkeypatch.setattr(pp, "stanza_available", False, raising=False)
    with pytest.raises(ImportError):
        pp.Preprocessor(engine="stanza")
