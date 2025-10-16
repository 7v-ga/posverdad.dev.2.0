# scrapy_project/items.py
from scrapy.item import Item, Field


class ArticleItem(Item):
    """
    Representa un artículo periodístico extraído por los spiders.

    Campos principales:
    - source:            nombre interno del medio (p. ej., "el_mostrador")
    - domain:            dominio inferido desde la URL (p. ej., "www.elmostrador.cl")
    - url:               URL canónica del artículo
    - title:             título del artículo
    - subtitle:          subtítulo si existe
    - body:              contenido del cuerpo del artículo (texto plano)
    - body_hash:         hash SHA-256 del body para detectar duplicados
    - publication_date:  fecha (YYYY-MM-DD)
    - published_at:      fecha/hora ISO (si la tienes), opcional
    - image:             URL de imagen principal si existe
    - authors:           lista de autores (str o dict normalizados)
    - keywords:          lista de palabras clave/tags del artículo
    - meta_description:  meta description SEO si existe
    - meta_keywords:     meta keywords SEO si existen
    - run_id:            identificador de la corrida/pipeline

    Salidas NLP (inyectadas por el pipeline/orquestador):
    - sentiment:         salida cruda del analizador (dict/obj/tupla según backend)
    - polarity:          score derivado de sentiment (float, [-1,1]) o None
    - subjectivity:      score de subjetividad (float, [0,1]) o None
    - entities:          lista de entidades: [{"text": "...", "label": "PER"}, ...]
    - framing:           dict con framing (p. ej., {"ideological_frame": "neutral"})
    - topics:            lista de tópicos si existieran (opcional)

    Nota: Si un spider usa 'author' o 'category', el pipeline debe normalizar a
    'authors' y 'categories' respectivamente (listas).
    """

    # Identificación / origen
    source = Field()     # nombre interno del medio (p. ej., "el_mostrador")
    domain = Field()     # dominio inferido desde la URL (p. ej., "www.elmostrador.cl")
    url = Field()        # URL canónica del artículo

    # Contenido principal
    title = Field()
    subtitle = Field()
    body = Field()
    image = Field()

    # Fechas
    publication_date = Field()  # YYYY-MM-DD
    published_at = Field()      # ISO datetime si existe

    # SEO / metadatos del documento
    meta_description = Field()
    meta_keywords = Field()

    # Colecciones / taxonomías
    authors = Field()     # list[str|dict]
    author = Field()      # alias transitorio (singular)
    keywords = Field()    # list[str]
    categories = Field()  # list[str]
    category = Field()    # alias transitorio (singular)

    # Hash / ejecución
    body_hash = Field()   # hash SHA-256 del body
    run_id = Field()      # identificador de la corrida/pipeline

    # Idioma (opcional)
    language = Field()

    # --- NLP (inyectado por pipeline/orquestador) ---
    sentiment = Field()      # estructura cruda del backend (dict/obj/tupla)
    polarity = Field()       # float | None
    subjectivity = Field()   # float | None
    entities = Field()       # list[{"text": str, "label": str}]
    framing = Field()        # dict (p. ej., {"ideological_frame": "neutral"})
    topics = Field()         # list[str] (opcional)