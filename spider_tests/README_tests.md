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
