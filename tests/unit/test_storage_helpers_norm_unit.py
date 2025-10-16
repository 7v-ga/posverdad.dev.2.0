import pytest
import re

# Importamos helpers "privados" directamente para pruebas unitarias focalizadas
from scrapy_project.storage_helpers import (
    _infer_domain_from_url,
    _normalize_meta_keywords_for_articles_field,
    _as_nullable_float,
)

# -----------------------------
# _infer_domain_from_url
# -----------------------------
@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://Example.com/Path?q=1", "example.com"),
        ("http://sub.Dominio.CL/page", "sub.dominio.cl"),
        ("", ""),                # vacío → string vacío
        (None, ""),             # None → string vacío
        ("not a url", ""),      # inválido → string vacío (función es tolerante)
    ],
)
def test_infer_domain_from_url(url, expected):
    assert _infer_domain_from_url(url) == expected


# -----------------------------
# _normalize_meta_keywords_for_articles_field
# -----------------------------
def _split_any(s: str) -> list[str]:
    """Split helper agnóstico al separador: coma/; | / y espacios."""
    parts = re.split(r"[,\|;/]", s)
    return [p.strip() for p in parts if p and p.strip()]

@pytest.mark.parametrize(
    "inp,expected_tokens_lower",
    [
        (None, []),                                   # None → falsy / sin tokens
        ("", []),                                     # vacío
        ("  , ,  ", []),                              # solo separadores/espacios
        ("a,b;c|d / e", ["a", "b", "c", "d", "e"]),   # mezcla de separadores
        (["  A  ", "b", "", "a "], ["a", "b"]),       # lista con espacios/duplicados (case-insensitive)
    ],
)
def test_normalize_meta_keywords_for_articles_field(inp, expected_tokens_lower):
    out = _normalize_meta_keywords_for_articles_field(inp)

    # Puede devolver "", None o un string con separador estándar; validamos por contenido
    if not expected_tokens_lower:
        assert not out  # None o "" aceptable
        return

    assert isinstance(out, str) and out.strip()
    tokens = _split_any(out)
    # normalizamos a lower para comparar sin importar mayúsculas/orden
    assert set(t.lower() for t in tokens) == set(expected_tokens_lower)


# -----------------------------
# _as_nullable_float
# -----------------------------
@pytest.mark.parametrize(
    "inp,expect_type,expect_value",
    [
        (None, type(None), None),         # None → None
        ("", type(None), None),           # vacío → None
        ("  ", type(None), None),         # espacios → None
        ("0.4", float, 0.4),              # string numérico → float
        (0.0, float, 0.0),                # numérico → mismo float
        ("-1", float, -1.0),              # entero string → float
        ("abc", type(None), None),        # inválido → None
    ],
)
def test_as_nullable_float_basic(inp, expect_type, expect_value):
    out = _as_nullable_float(inp)
    assert (out is None and expect_type is type(None)) or isinstance(out, expect_type)
    if isinstance(out, float):
        assert out == pytest.approx(expect_value, rel=1e-6)
