# === Utilidades y limpieza ===
.PHONY: clean clean-logs clean-graphs clean-outputs clean-caches clean-all \
        freeze freeze-lock retry-bad-dates audit env-setup

# Herramientas (defaults seguros; se pueden sobreescribir desde el Makefile raíz)
VENV    ?= .venv
PYTHON  ?= $(VENV)/bin/python
PIP     ?= $(VENV)/bin/pip
UV      ?= uv

clean-logs: ## Borrar logs antiguos
	@echo "🧿 Limpiando logs antiguos..."
	@find logs -type f -name '*.log' -delete 2>/dev/null || true

clean-graphs: ## Borrar gráficos (PNG/SVG) generados
	@echo "🧿 Limpiando gráficos anteriores..."
	@find graphs -type f \( -name '*.png' -o -name '*.svg' \) -delete 2>/dev/null || true

clean-outputs: ## Borrar outputs generados
	@echo "🧹 Limpiando outputs..."
	@rm -rf outputs 2>/dev/null || true

clean-caches: ## Borrar caches de Python/pytest/linters
	@echo "🧽 Limpiando caches..."
	@find . -type d -name '__pycache__' -prune -exec rm -rf {} + 2>/dev/null || true
	@rm -rf .pytest_cache .mypy_cache .ruff_cache .cache htmlcov .coverage 2>/dev/null || true

clean: clean-logs clean-graphs ## Limpieza rápida (logs + graphs)

clean-all: clean-logs clean-graphs clean-outputs clean-caches ## Limpieza completa

freeze: ## Congelar deps a requirements.txt (flujo clásico con pip)
	@echo "📌 Congelando dependencias en requirements.txt..."
	@$(PIP) freeze > requirements.txt

freeze-lock: ## Generar lock reproducible (si usas pyproject + uv)
	@if [ -f pyproject.toml ]; then \
	  echo "🔒 Generando requirements.lock.txt con uv..."; \
	  $(UV) pip compile pyproject.toml -o requirements.lock.txt --all-extras --generate-hashes; \
	else \
	  echo "⚠️  No hay pyproject.toml; omitiendo freeze-lock"; \
	fi

retry-bad-dates: ## Reintentar artículos con fechas problemáticas
	@$(PYTHON) scripts/retry_bad_dates.py

audit: ## Auditoría de integridad del pipeline
	@$(PYTHON) scripts/auditor_pipeline_integridad.py

env-setup: ## Script de entorno (si lo usas)
	@bash -eu setup_env.sh
