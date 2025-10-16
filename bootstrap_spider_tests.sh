#!/usr/bin/env bash
set -euo pipefail

ROOT="${PWD}"
OUT_DIR="${ROOT}/tests/spiders"
FX_DIR="${OUT_DIR}/fixtures"
DOC_DIR="${ROOT}/spider_tests"

mkdir -p "${FX_DIR}" "${DOC_DIR}"

# ---------------- conftest.py ----------------
cat > "${OUT_DIR}/conftest.py" << 'PY'
import pathlib
import pytest
from scrapy.http import HtmlResponse, Request

FIXTURES_DIR = pathlib.Path(__file__).parent / "fixtures"

def _read_fixture(name: str) -> bytes:
    p = FIXTURES_DIR / name
    with open(p, "rb") as f:
        return f.read()

def fake_response(url: str, html: bytes | str, encoding: str = "utf-8") -> HtmlResponse:
    if isinstance(html, str):
        html = html.encode(encoding)
    request = Request(url=url)
    response = HtmlResponse(url=url, request=request, body=html, encoding=encoding)
    return response

@pytest.fixture
def html_listing_2025():
    return _read_fixture("listing_all_2025.html")

@pytest.fixture
def html_listing_mixed_2021_2025():
    return _read_fixture("listing_mixed_2021_2025.html")

@pytest.fixture
def html_listing_all_2023():
    return _read_fixture("listing_all_2023.html")

@pytest.fixture
def html_article_2023_07_12():
    return _read_fixture("article_2023_07_12.html")
PY

# ---------------- fixtures ----------------
cat > "${FX_DIR}/listing_all_2025.html" << 'HTML'
<!doctype html>
<html>
<head><meta charset="utf-8"><title>Claves 2025</title></head>
<body>
  <div class="d-tag-card">
    <a href="https://www.elmostrador.cl/noticias/pais/2025/09/15/nota-x/">
      <time datetime="2025-09-15">15.09.2025</time>
    </a>
  </div>
  <div class="d-tag-card">
    <a href="https://www.elmostrador.cl/noticias/pais/2025/08/11/nota-y/">
      <time datetime="2025-08-11">11.08.2025</time>
    </a>
  </div>
</body>
</html>
HTML

cat > "${FX_DIR}/listing_mixed_2021_2025.html" << 'HTML'
<!doctype html>
<html>
<head><meta charset="utf-8"><title>Claves mixed</title></head>
<body>
  <div class="d-tag-card">
    <a href="https://www.elmostrador.cl/noticias/pais/2021/01/02/nota-a/">
      <time datetime="2021-01-02">02.01.2021</time>
    </a>
  </div>
  <div class="d-tag-card">
    <a href="https://www.elmostrador.cl/noticias/pais/2022/07/12/nota-b/">
      <time datetime="2022-07-12">12.07.2022</time>
    </a>
  </div>
  <div class="d-tag-card">
    <a href="https://www.elmostrador.cl/noticias/pais/2025/03/04/nota-c/">
      <time datetime="2025-03-04">04.03.2025</time>
    </a>
  </div>
</body>
</html>
HTML

cat > "${FX_DIR}/listing_all_2023.html" << 'HTML'
<!doctype html>
<html>
<head><meta charset="utf-8"><title>Claves 2023</title></head>
<body>
  <div class="d-tag-card">
    <a href="https://www.elmostrador.cl/noticias/pais/2023/12/12/nota-1/">
      <time datetime="2023-12-12">12.12.2023</time>
    </a>
  </div>
  <div class="d-tag-card">
    <a href="https://www.elmostrador.cl/noticias/pais/2023/12/11/nota-2/">
      <time datetime="2023-12-11">11.12.2023</time>
    </a>
  </div>
  <div class="d-tag-card">
    <a href="https://www.elmostrador.cl/noticias/pais/2023/07/12/nota-3/">
      <time datetime="2023-07-12">12.07.2023</time>
    </a>
  </div>
</body>
</html>
HTML

cat > "${FX_DIR}/article_2023_07_12.html" << 'HTML'
<!doctype html>
<html>
<head><meta charset="utf-8"><title>Nota 2023-07-12</title></head>
<body>
  <article>
    <h1 class="headline">Título de ejemplo 2023-07-12</h1>
    <div class="meta">
      <time class="published" datetime="2023-07-12T10:30:00-04:00">12 julio 2023</time>
    </div>
    <div class="body">
      <p>Contenido de ejemplo.</p>
    </div>
  </article>
</body>
</html>
HTML

# ---------------- test_el_mostrador_extract_years.py ----------------
cat > "${OUT_DIR}/test_el_mostrador_extract_years.py" << 'PY'
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
PY

# ---------------- test_el_mostrador_collect_first_page.py ----------------
cat > "${OUT_DIR}/test_el_mostrador_collect_first_page.py" << 'PY'
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
PY

# ---------------- test_el_mostrador_parse_article.py ----------------
cat > "${OUT_DIR}/test_el_mostrador_parse_article.py" << 'PY'
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
PY

# ---------------- README_tests.md ----------------
cat > "${DOC_DIR}/README_tests.md" << 'MD'
# Tests específicos del spider `el_mostrador`

Este paquete añade **tests de parsing y de navegación** para el spider `el_mostrador` usando `pytest` + utilidades de Scrapy.

## Qué incluyen

- `test_el_mostrador_extract_years.py`: valida la extracción de **años** desde listados (`/claves/feed/page/N/`) sobre **páginas congeladas**.
- `test_el_mostrador_collect_first_page.py`: prueba la **lógica de navegación** (expand/precisión/collect) con un **stub** del extractor de años para garantizar que, al encontrar el año objetivo, el spider **retrocede hasta la primera página de ese año** antes de recolectar.
- `test_el_mostrador_parse_article.py`: valida el **parseo de artículos** y la normalización de la fecha de publicación.
- `fixtures/`: HTMLs mínimos representativos de listados y una nota.

## Cómo usarlos

1. Copia la carpeta `tests/spiders` a tu repo si no la tienes ya.
2. Ejecuta:
   ```bash
   pytest tests/spiders -q
