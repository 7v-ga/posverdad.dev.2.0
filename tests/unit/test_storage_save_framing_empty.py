from scrapy_project.storage_helpers import save_framing

def test_save_framing_early_returns():
    # Simplemente no debe fallar ni ejecutar SQL
    save_framing(object(), 1, None)
    save_framing(object(), 1, {})
