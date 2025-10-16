from datetime import datetime
from scrapy_project.spiders.el_mostrador import ElMostradorSpider

def test_article_date_parsing(fake_response, html_article_2023_07_12):
    spider = ElMostradorSpider(year=2023)
    resp = fake_response("https://www.elmostrador.cl/noticias/pais/2023/07/12/nota-3/", html_article_2023_07_12)
    parse_article = getattr(spider, "parse_article", None) or getattr(spider, "_parse_article", None)
    assert callable(parse_article), "El spider debe exponer parse_article(response)"
    items = list(parse_article(resp))
    assert items, "parse_article() debería emitir al menos un item"
    item = items[0]
    published = item.get("published_at") or item.get("date") or item.get("published") or item.get("publication_date")
    assert published, f"El item debe incluir fecha de publicación. Keys: {list(item.keys())}"
    if isinstance(published, str):
        assert published.startswith("2023-07-12"), f"Esperaba ISO empezando por 2023-07-12, obtuve {published}"
    else:
        assert isinstance(published, datetime)
        assert published.date().isoformat() == "2023-07-12"
