import pathlib
import pytest
from scrapy.http import HtmlResponse, Request

FIXTURES_DIR = pathlib.Path(__file__).parent / "fixtures"

def _read_fixture(name: str) -> bytes:
    p = FIXTURES_DIR / name
    with open(p, "rb") as f:
        return f.read()

def _make_fake_response(url: str, html: bytes | str, encoding: str = "utf-8") -> HtmlResponse:
    if isinstance(html, str):
        html = html.encode(encoding)
    request = Request(url=url)
    response = HtmlResponse(url=url, request=request, body=html, encoding=encoding)
    return response


@pytest.fixture
def fake_response():
    """Entrega una fábrica de HtmlResponse: fake_response(url, html, encoding='utf-8')."""
    from scrapy.http import HtmlResponse, Request
    def _factory(url: str, html: bytes | str, encoding: str = "utf-8") -> HtmlResponse:
        return _make_fake_response(url, html, encoding)
    return _factory

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
