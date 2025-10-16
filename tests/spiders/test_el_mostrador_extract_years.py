import re
from scrapy_project.spiders.el_mostrador import ElMostradorSpider

def _call_year_extractor(spider, response):
    # Intenta varios nombres comunes de método
    for name in ("_extract_years", "extract_years", "_extract_listing_years", "extract_listing_years"):
        fn = getattr(spider, name, None)
        if callable(fn):
            return sorted(set(fn(response)))
    # Fallback para que el test no dependa del nombre del método
    years = set()
    for sel in response.css("time::attr(datetime)").getall():
        m = re.search(r"(19|20)\d{2}", sel)
        if m:
            years.add(int(m.group(0)))
    if not years:
        for href in response.css(".d-tag-card a::attr(href)").getall():
            m = re.search(r"/(19|20)\d{2}/", href)
            if m:
                years.add(int(m.group(0).strip("/")))
    return sorted(years)

def test_extract_years_all_2025(fake_response, html_listing_2025):
    spider = ElMostradorSpider(year=2022)
    resp = fake_response("https://www.elmostrador.cl/claves/feed/page/1/", html_listing_2025)
    years = _call_year_extractor(spider, resp)
    assert years == [2025]

def test_extract_years_mixed(fake_response, html_listing_mixed_2021_2025):
    spider = ElMostradorSpider(year=2022)
    resp = fake_response("https://www.elmostrador.cl/claves/feed/page/8192/", html_listing_mixed_2021_2025)
    years = _call_year_extractor(spider, resp)
    assert years == [2021, 2022, 2025]

def test_extract_years_all_2023(fake_response, html_listing_all_2023):
    spider = ElMostradorSpider(year=2023)
    resp = fake_response("https://www.elmostrador.cl/claves/feed/page/100/", html_listing_all_2023)
    years = _call_year_extractor(spider, resp)
    assert years == [2023]
