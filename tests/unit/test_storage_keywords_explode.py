from scrapy_project.storage_helpers import _explode_keywords

def test_explode_keywords_mixed_separators_and_lists():
    s = "a, b|c; d/e , ,"
    lst = ["x, y", " z|w ", "v / u"]
    out1 = _explode_keywords(s)
    out2 = _explode_keywords(lst)
    assert out1 == ["a", "b", "c", "d", "e"]
    assert out2 == ["x", "y", "z", "w", "v", "u"]
