import pytest
from unittest.mock import MagicMock

def test_analyzer_init_failure_sets_sa_none_and_returns_none(monkeypatch):
    # Forzamos que pysentimiento falle al crear el analyzer
    import scrapy_project.nlp_transformers as mod
    monkeypatch.setattr(
        mod,
        "create_analyzer",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    # Sin reload: mantenemos el monkeypatch activo
    nlp = mod.PosverdadNLP(nlp_model=None)

    # Debe tolerar la ausencia de analyzer
    assert getattr(nlp, "sa", None) is None
    pol, score = nlp.analyze_sentiment("hola mundo")
    assert pol is None and score is None


def test_analyze_sentiment_none_when_blank_text(monkeypatch):
    import scrapy_project.nlp_transformers as mod
    nlp = mod.PosverdadNLP(nlp_model=None)
    # Aseguramos que SA exista para diferenciar el early return del caso anterior
    nlp.sa = MagicMock()
    pol, score = nlp.analyze_sentiment("   ")
    assert pol is None and score is None
