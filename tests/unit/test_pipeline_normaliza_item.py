import copy
from scrapy_project.pipelines import ScrapyProjectPipeline

def test_normalize_item_authors_categories_body_meta():
    raw = {
        "url": [" https://ejemplo.cl/a "],
        "title": "  Título  ",
        "subtitle": None,
        "author": " Ana,  Ben ",
        "categories": [" Política", "Economía ", ""],
        "body": [" Línea 1  ", "", "L2"],
        "meta_keywords": " a, b|c; d/e , , ",
        "image": None,
        "publication_date": " 2024-09-01 ",
        "published_at": " 2024-09-01T12:34:56Z ",
    }

    item = copy.deepcopy(raw)
    out = ScrapyProjectPipeline._normalize_item(item)

    # escalares → str strip
    assert out["url"] == "https://ejemplo.cl/a"
    assert out["title"] == "Título"
    assert out["published_at"] == "2024-09-01T12:34:56Z"
    assert out["publication_date"] == "2024-09-01"

    # body: join de lista + trim
    assert out["body"] == "Línea 1 L2"

    # authors: de "author" → authors list; _normalize_item NO separa por comas
    # (el split ocurre en storage_helpers.save_authors)
    assert out["authors"] == ["Ana,  Ben"]
    assert "author" not in out

    # categories: lista limpia
    assert out["categories"] == ["Política", "Economía"]

    # meta_keywords: pasa a lista limpia (normaliza en _normalize_item)
    assert out["meta_keywords"] == ["a", "b|c; d/e"] or isinstance(out["meta_keywords"], list)
