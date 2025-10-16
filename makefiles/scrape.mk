# === Scraping y procesamiento ===
.PHONY: scrape scrape-json pre-scrape

# Heredadas de env.mk
VENV    ?= .venv
PYTHON  ?= $(VENV)/bin/python

# Antes de scrapear: limpiar, crear logs/graphs y correr tests básicos
pre-scrape: ## Limpia y verifica stack antes de scrapear
	@mkdir -p logs graphs
	@$(MAKE) -s clean-logs
	@$(MAKE) -s clean-graphs
	@$(MAKE) -s test-store-article
	@$(MAKE) -s test

scrape: pre-scrape ## Ejecuta spider principal (usa ARGS="...")
	@echo "🕷️  Corriendo spider el_mostrador $(ARGS)"
	@$(VENV)/bin/scrapy crawl el_mostrador $(ARGS)

# Exporta en JSON (usa -o/FEED export; puedes pasar ARGS="..." para filtros)
scrape-json: ## Ejecuta spider y exporta a output.json
	@echo "🕷️  Corriendo spider el_mostrador → output.json"
	@$(VENV)/bin/scrapy crawl el_mostrador $(ARGS) -o output.json

# ⚠️ IMPORTANTE: no redefinir 'reset' aquí para evitar colisión con el Makefile raíz.
# Si quieres un “reset” específico de scraping, usa otro nombre, por ejemplo:
scrape-reset: ## Resetea entorno mínimo para scraping (DB y modelos)
	@$(MAKE) -s init-db-reset
	@$(MAKE) -s spacy-model
