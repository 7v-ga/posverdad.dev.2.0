import os
from dotenv import load_dotenv

load_dotenv()

BOT_NAME = "scrapy_project"

SPIDER_MODULES = ["scrapy_project.spiders"]
NEWSPIDER_MODULE = "scrapy_project.spiders"

# Desactiva logging de Scrapy para usar tu logger personalizado
LOG_ENABLED = True

# Codificación de exportación
FEED_EXPORT_ENCODING = "utf-8"

# Pipelines
# Habilitar pipeline (asegúrate que el archivo/clase existen exactamente con ese path/nombre)
ITEM_PIPELINES = {
    "scrapy_project.pipelines.ScrapyProjectPipeline": 300,
}

# (opcional) Ajusta niveles de log de Scrapy para ver mid/pipelines claramente
LOG_LEVEL = "INFO"


# Variables de entorno para conexión PostgreSQL
POSTGRES_DB = os.getenv("POSTGRES_DB", "postverdad")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

# Respeta o no robots.txt
ROBOTSTXT_OBEY = True  # Cambiar a False si haces scraping investigativo

# Control de concurrencia (opcional)
CONCURRENT_REQUESTS = int(os.getenv("CONCURRENT_REQUESTS", "8"))
# DOWNLOAD_DELAY = 1.5

# Headers por defecto (opcional)
# DEFAULT_REQUEST_HEADERS = {
#     "User-Agent": "Mozilla/5.0 (compatible; PostverdadBot/1.0; +http://postverdad.local)",
#     "Accept-Language": "es-ES,es;q=0.9",
# }

# Autothrottle (opcional)
# AUTOTHROTTLE_ENABLED = True
# AUTOTHROTTLE_START_DELAY = 2
# AUTOTHROTTLE_MAX_DELAY = 30
# AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0

# HTTP caching, middlewares (a futuro)
# HTTPCACHE_ENABLED = True
