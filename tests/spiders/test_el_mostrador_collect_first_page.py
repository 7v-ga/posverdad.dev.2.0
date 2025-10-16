from scrapy.http import HtmlResponse, Request
from scrapy_project.spiders.el_mostrador import ElMostradorSpider

def _page_from(url: str) -> int:
    try:
        return int(url.rstrip("/").split("/")[-1])
    except Exception:
        return -1

def test_precision_backtracks_to_first_page_of_year(monkeypatch):
    """
    Simula la navegación sin depender del DOM.
    Esperamos que para target_year=2023 el spider retroceda hasta la primera
    página de ese año (6500) antes de cambiar a 'collect'.
    """
    def fake_years_for_page(n: int):
        if n < 2000:
            return [2025]
        if n < 4000:
            return [2024, 2025]
        if n < 6500:
            return [2023, 2025]  # 2023 presente, pero aún hay páginas anteriores de 2023
        if n < 7000:
            return [2023]        # primeras páginas de 2023 (más antiguas)
        if n < 9000:
            return [2021, 2023]
        return [2019, 2021]

    spider = ElMostradorSpider(year=2023)

    # Stub del extractor de años (tolera distintos nombres)
    def _stub_extract_years(response):
        n = _page_from(response.url)
        return fake_years_for_page(n)

    for name in ("_extract_years", "extract_years", "_extract_listing_years", "extract_listing_years"):
        if hasattr(spider, name):
            monkeypatch.setattr(spider, name, _stub_extract_years, raising=False)

    current = Request(url="https://www.elmostrador.cl/claves/feed/page/1/", dont_filter=True)
    steps = 0
    collect_at_page = None

    while steps < 200:
        resp = HtmlResponse(url=current.url, request=current, body=b"<html></html>", encoding="utf-8")
        out = list(spider.parse(resp))
        assert out, "parse() no produjo Requests; revisa la lógica del spider"

        next_req = next((o for o in out if isinstance(o, Request)), None)
        assert next_req is not None, "parse() debería ir navegando entre páginas"

        meta = getattr(next_req, "meta", {})
        page = _page_from(next_req.url)
        phase = str(meta.get("phase") or meta.get("mode") or meta.get("state") or "").lower()
        if phase in ("collect", "recolectar"):
            collect_at_page = page
            break

        current = next_req
        steps += 1

    assert collect_at_page is not None, "El spider nunca pasó a 'collect'"
    assert collect_at_page == 6500, f"Debe iniciar 'collect' en la primera página del año (6500), no en {collect_at_page}"
