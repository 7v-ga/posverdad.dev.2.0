from scrapy_project.storage_helpers import save_authors

def test_save_authors_early_returns():
    # No debe lanzar ni tocar DB para estos inputs vacíos
    save_authors(object(), 1, None)
    save_authors(object(), 1, "")
    save_authors(object(), 1, [])
