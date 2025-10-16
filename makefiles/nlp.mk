# === Modelos y utilidades NLP ===
.PHONY: setup-nlp nlp-warmup spacy-validate spacy-download-md spacy-download-lg \
        stanza-install test-stanza

# Heredadas de env.mk
VENV    ?= .venv
PYTHON  ?= $(VENV)/bin/python
PIP     ?= $(VENV)/bin/pip
UV      ?= uv

# --- Warmup general de NLP ---
setup-nlp: ## Fix de NLTK/SSL (si aplica) + warmup NLP
	@bash scripts/fix_nltk_ssl.sh $(PYTHON)
	@$(PYTHON) scripts/nlp_warmup.py

nlp-warmup: ## Solo warmup NLP (carga modelos, etc.)
	@$(PYTHON) scripts/nlp_warmup.py

# --- spaCy: validación e instalación de modelos ---
spacy-validate: ## Validar que spaCy y es_core_news_md cargan correctamente
	@. $(VENV)/bin/activate && \
	$(PYTHON) -c "import spacy, sys; print('spaCy:', spacy.__version__, '| Python:', sys.version); spacy.load('es_core_news_md'); print('✔ es_core_news_md OK')"

# Si prefieres descargar desde aquí (además de env.mk), deja estos targets:
spacy-download-md: ## Descargar modelo spaCy md
	@. $(VENV)/bin/activate && $(UV) pip install \
		\"es_core_news_md @ https://github.com/explosion/spacy-models/releases/download/es_core_news_md-3.8.0/es_core_news_md-3.8.0.tar.gz\"
	@$(MAKE) -s spacy-validate

spacy-download-lg: ## Descargar modelo spaCy lg (opcional)
	@. $(VENV)/bin/activate && $(UV) pip install \
		\"es_core_news_lg @ https://github.com/explosion/spacy-models/releases/download/es_core_news_lg-3.8.0/es_core_news_lg-3.8.0.tar.gz\"
	@. $(VENV)/bin/activate && \
	$(PYTHON) -c "import spacy; spacy.load('es_core_news_lg'); print('✔ es_core_news_lg OK')"

# --- Stanza ---
stanza-install: ## Instalar Stanza y modelo ES
	@. $(VENV)/bin/activate && $(UV) pip install stanza
	@. $(VENV)/bin/activate && $(PYTHON) -c "import stanza; stanza.download('es'); print('✔ stanza[es] OK')"

# Usa cobertura con el coverage del venv, evita $(ENV) que no existe.
test-stanza: spacy-validate status-db stanza-install ## Tests con Stanza y cobertura
	@mkdir -p logs
	@echo "🧲 Ejecutando tests usando Stanza con cobertura..."
	@. $(VENV)/bin/activate && \
	PYTHONPATH=$(shell pwd) COVERAGE_FILE=.coverage.stanza \
	$(VENV)/bin/coverage run -m pytest tests --engine=stanza | tee logs/test_stack_stanza.log
	@. $(VENV)/bin/activate && $(VENV)/bin/coverage report -m --data-file=.coverage.stanza
	@$(MAKE) -s merge-coverage
	@$(MAKE) -s coverage-html
