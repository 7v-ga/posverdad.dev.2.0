from scrapy_project.storage_helpers import _as_nullable_float

def test_as_nullable_float_dict_invalids():
    assert _as_nullable_float({"value": "NaN"}) is None
    assert _as_nullable_float({"value": "inf"}) is None
    assert _as_nullable_float({"value": ""}) is None
