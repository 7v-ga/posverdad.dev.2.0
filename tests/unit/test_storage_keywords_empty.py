from scrapy_project.storage_helpers import save_keywords

def test_save_keywords_early_returns():
    # No debe lanzar ni tocar DB para entradas vacías
    save_keywords(object(), 1, None)
    save_keywords(object(), 1, "")
    save_keywords(object(), 1, [])
    # Caso con solo separadores → _explode_keywords produce []
    save_keywords(object(), 1, " , ; | / ")
