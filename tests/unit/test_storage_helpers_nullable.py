# tests/unit/test_storage_helpers_nullable.py
from scrapy_project.storage_helpers import _as_nullable_float

def test_nullable_float_cases():
    assert _as_nullable_float(None) is None
    assert _as_nullable_float({"value": "0.5"}) == 0.5
    assert _as_nullable_float("  ") is None
    assert _as_nullable_float("NaN") is None
    assert _as_nullable_float("-1") == -1.0

def test_nullable_float_handles_infinities():
    from scrapy_project.storage_helpers import _as_nullable_float

    # floats no finitos
    assert _as_nullable_float(float("inf")) is None
    assert _as_nullable_float(float("-inf")) is None

    # cadenas no finitas (case-insensitive)
    assert _as_nullable_float("inf") is None
    assert _as_nullable_float("-inf") is None
    assert _as_nullable_float("Infinity") is None
    assert _as_nullable_float("-Infinity") is None
