# === Tests y cobertura ===
.PHONY: test test-unit test-int coverage-html cov-clean merge-coverage test-store-article test-storage

# Selección por defecto del alcance de test: unit | integration | all
DEFAULT_TEST_SCOPE ?= unit  # cambia a 'all' si prefieres suite completa por defecto

# Heredadas (o por defecto)
VENV      ?= .venv
PYTHON    ?= $(VENV)/bin/python
PYTEST    ?= $(VENV)/bin/pytest
COVERAGE  ?= $(VENV)/bin/coverage

# Verifica que coverage esté instalado (sin here-doc)
_ensure-coverage:
	@$(PYTHON) -c "import coverage" 2>/dev/null || { \
	  echo "❌ 'coverage' no está instalado en $(VENV). Ejecuta:"; \
	  echo "   make install-dev   # o pip/uv install coverage pytest pytest-cov"; \
	  exit 1; }

# ------------------ Dispatcher según DEFAULT_TEST_SCOPE ------------------
# Importante: envolver la definición completa del target con ifeq/else/endif

ifeq ($(DEFAULT_TEST_SCOPE),unit)
test: spacy-model _ensure-coverage ## Tests con cobertura (solo unit)
	@$(MAKE) -s test-unit
else ifeq ($(DEFAULT_TEST_SCOPE),integration)
test: spacy-model _ensure-coverage ## Tests con cobertura (solo integración)
	@$(MAKE) -s test-int
else
test: spacy-model _ensure-coverage ## Tests con cobertura (suite completa)
	@mkdir -p logs
	@echo "🧲 Ejecutando suite completa con cobertura..."
	@$(PYTEST) | tee logs/test_stack.log
	@$(COVERAGE) report -m || true
	@echo "📊 Log: logs/test_stack.log"
endif
# ------------------------------------------------------------------------

# Solo unit (rápidos, sin depender de DB)
test-unit: ## Ejecuta solo tests unitarios (marcados con -m unit)
	@$(PYTEST) -m unit

# Solo integración (AHORA sin dependencia implícita a db-up)
# Nota: 'reset-all' ya levanta la DB antes de llamar a test-int.
test-int: ## Ejecuta solo tests de integración (acumula cobertura sobre unit)
	@$(PYTEST) -m integration --cov-append

# Reporte HTML de cobertura (usa .coverage existente)
coverage-html: _ensure-coverage ## Reporte HTML de cobertura
	@$(COVERAGE) html
	@echo "🌐 Reporte HTML en htmlcov/index.html"

# Limpia archivos de cobertura
cov-clean: ## Limpia artefactos de cobertura
	@rm -rf .coverage .coverage.* htmlcov htmlcov-* || true
	@echo "🧹 Cobertura limpia"

# Combina coberturas y genera HTML combinado (útil si corres runs separados, p.ej. spaCy/Stanza)
merge-coverage: _ensure-coverage ## Fusiona coberturas y genera HTML combinado
	@echo "🦬 Unificando reportes de cobertura..."
	@COVERAGE_FILE=.coverage.stanza $(COVERAGE) combine --append .coverage || true
	@$(COVERAGE) report -m
	@$(COVERAGE) html -d htmlcov-merged
	@echo "🌐 Reporte HTML combinado: htmlcov-merged/index.html"

# Atajo: test de integración de store_article (SIN db-up aquí)
test-store-article: ## Test de integración de store_article
	@echo "🧪 Ejecutando test de integración de store_article..."
	@$(PYTEST) -q tests/integration/test_store_article.py --cov-append -o cov_fail_under=0 || echo "⚠️ test_store_article falló (no bloquea)"

# Tests de integración de storage (SIN db-up)
test-storage: ## Tests de integración de storage (con log)
	@mkdir -p logs
	@$(PYTEST) tests/integration/test_storage.py | tee logs/test_storage.log
