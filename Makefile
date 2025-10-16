# =============================================================================
# Makefile — Posverdad (raíz)
# =============================================================================
# Uso:
#   make help
#   make reset-all              # DROP+CREATE schema + seed (obligatorio)
#   make dev-up / make dev-down # docker compose up/down
#   make seed                   # aplicar seed (db-seed)
# =============================================================================

SHELL := /bin/bash
MAKEFLAGS += --no-builtin-rules --no-print-directory

# Proyecto (opcional)
PROJECT        ?= posverdad
PYTHON         ?= python3

# Archivos clave que algunos .mk usan
SCHEMA_FILE    ?= schema.sql
SEED_FILE      ?= db/seed_entities_aux.sql
INIT_DB_SCRIPT ?= init_db.py

# =============================================================================
# Includes (layout modular en makefiles/*.mk)
# =============================================================================
-include makefiles/env.mk
-include makefiles/util.mk
-include makefiles/db.mk
-include makefiles/nlp.mk
-include makefiles/scrape.mk
-include makefiles/report.mk
-include makefiles/notify.mk
-include makefiles/test.mk
-include makefiles/reconcile.mk

# =============================================================================
# Ayuda
# =============================================================================
.DEFAULT_GOAL := help

.PHONY: help
help: ## Mostrar esta ayuda
	@echo ""
	@echo "🧭  $(PROJECT) — Targets disponibles"
	@echo "------------------------------------------------------------"
	@grep -h -E '^[[:alnum:]_./-]+:.*##' $(MAKEFILE_LIST) \
	| awk 'BEGIN {FS = ":.*##"; OFS = ""} {printf "  \033[36m%-28s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Sugerencias:"
	@echo "  • make reset-all                 (reset esquema + seed)"
	@echo "  • make dev-up / dev-down         (docker compose)"
	@echo "  • make seed                      (aplicar seed_entities_aux.sql)"
	@echo "  • make doctor                    (estado/conexión DB)"
	@echo ""

# =============================================================================
# Orquestación top-level
# =============================================================================

.PHONY: reset-all
reset-all: compose-reset db-up init-db-reset db-seed ## Reset DB (DROP+CREATE), aplica schema y seed (obligatorio)
	@echo "✅ Reset completo: schema + seed"

.PHONY: seed
seed: db-seed ## Aplicar únicamente el seed (db-seed)

.PHONY: dev-up
dev-up: compose-up ## Levantar stack de desarrollo con docker compose

.PHONY: dev-down
dev-down: compose-down ## Bajar stack de desarrollo con docker compose

.PHONY: doctor
doctor: status-db ## Ver estado y conexión de la base de datos
