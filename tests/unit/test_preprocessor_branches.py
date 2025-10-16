import pytest

def test_preprocess_stanza_unavailable_raises(monkeypatch):
    import scrapy_project.preprocessor as mod
    # Forzamos que stanza no esté disponible en el módulo
    monkeypatch.setattr(mod, "stanza_available", False, raising=False)

    # Dependiendo de tu implementación, el ImportError puede lanzarse en __init__ o en preprocess.
    with pytest.raises(ImportError) as exc:
        pre = mod.Preprocessor(engine="stanza")
        pre.preprocess("texto")
    # Refuerzo: aseguramos que el mensaje apunte a Stanza
    assert "stanza" in str(exc.value).lower()


def test_preprocessor_unknown_engine_raises_value_error():
    import scrapy_project.preprocessor as mod
    # Engine desconocido → debe levantar ValueError (cubre branch 50->exit)
    with pytest.raises(ValueError):
        mod.Preprocessor(engine="desconocido")
