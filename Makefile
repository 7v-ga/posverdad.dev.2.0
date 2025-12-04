# =============================================================================
# Makefile — Posverdad (raíz)
# =============================================================================
# Uso:
#   make help
#   make reset-all              # DROP+CREATE schema + seed (obligatorio)
#   make dev-up / make dev-down # docker compose up/down
#   make seed                   # aplicar seed (db-seed)
#   make web-dev                # levantar Next.js en apps/web
#   make web-doctor             # chequeos rápidos de apps/web
# =============================================================================

SHELL := /bin/bash
MAKEFLAGS += --no-builtin-rules --no-print-directory

# Proyecto (opcional)
PROJECT         ?= posverdad
PYTHON          ?= python3
PNPM            ?= pnpm

# Rutas y archivos clave
SCHEMA_FILE     ?= db/schema.sql
SEED_FILE       ?= db/seed_entities_aux.sql
INIT_DB_SCRIPT  ?= db/init_db.py

# Frontend (nuevo layout)
WEB_DIR         ?= apps/web
WEB_ENV         ?= $(WEB_DIR)/.env.local
WEB_TSCONFIG    ?= $(WEB_DIR)/tsconfig.json
WEB_NEXTCONF    ?= $(WEB_DIR)/next.config.ts

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
	@grep -h -E '^[[:alnum:]_./-]+:.*##' $(MAKEFILE_LIST) 2>/dev/null \
	| awk 'BEGIN {FS = ":.*##"; OFS = ""} {printf "  \033[36m%-28s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Sugerencias:"
	@echo "  • make reset-all                 (reset esquema + seed)"
	@echo "  • make dev-up / dev-down         (docker compose)"
	@echo "  • make web-dev                   (Next.js en apps/web)"
	@echo "  • make web-doctor                (chequeos rápidos frontend)"
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

# =============================================================================
# Backend (apps/api) — utilidades
# =============================================================================

.PHONY: api-dev
api-dev:  ## Levantar FastAPI en modo desarrollo
	@$(PYTHON) -m uvicorn apps.api.main:app --reload --host 0.0.0.0 --port 8000

# =============================================================================
# Frontend (apps/web) — utilidades
# =============================================================================

.PHONY: web-install
web-install: ## Instalar dependencias del frontend (apps/web)
	@$(PNPM) -C $(WEB_DIR) install

.PHONY: web-dev
web-dev: ## Levantar Next.js (apps/web)
	@$(PNPM) -C $(WEB_DIR) dev

.PHONY: web-build
web-build: ## Build de producción (apps/web)
	@$(PNPM) -C $(WEB_DIR) build

.PHONY: web-start
web-start: ## Servir build de producción (apps/web)
	@$(PNPM) -C $(WEB_DIR) start

.PHONY: web-typecheck
web-typecheck: ## Typecheck TypeScript (apps/web)
	@$(PNPM) -C $(WEB_DIR) typecheck

.PHONY: web-lint
web-lint: ## Lint frontend (apps/web)
	@$(PNPM) -C $(WEB_DIR) lint

.PHONY: web-format
web-format: ## Formatear código (apps/web)
	@$(PNPM) -C $(WEB_DIR) format

# =============================================================================
# Sanity checks
# =============================================================================

.PHONY: check-paths
check-paths: ## Verificar paths críticos (schema/seed/init y web dir)
	@test -f "$(SCHEMA_FILE)" || (echo "❌ No existe $(SCHEMA_FILE)"; exit 1)
	@test -f "$(SEED_FILE)"   || (echo "❌ No existe $(SEED_FILE)"; exit 1)
	@test -f "$(INIT_DB_SCRIPT)" || (echo "❌ No existe $(INIT_DB_SCRIPT)"; exit 1)
	@test -d "$(WEB_DIR)"     || (echo "❌ No existe $(WEB_DIR)"; exit 1)
	@echo "✅ Paths OK:"
	@echo "   - SCHEMA_FILE:     $(SCHEMA_FILE)"
	@echo "   - SEED_FILE:       $(SEED_FILE)"
	@echo "   - INIT_DB_SCRIPT:  $(INIT_DB_SCRIPT)"
	@echo "   - WEB_DIR:         $(WEB_DIR)"

# =============================================================================
# Web doctor — chequeos rápidos de apps/web
# =============================================================================

.PHONY: web-doctor
web-doctor: ## Chequeos de entorno FE (env, lockfile duplicado, tsconfig, typecheck)
	@echo "🔎 web-doctor: Revisando $(WEB_DIR)"
	@if [ ! -d "$(WEB_DIR)" ]; then echo "❌ No existe $(WEB_DIR)"; exit 1; fi
	@if [ -f "$(WEB_DIR)/pnpm-lock.yaml" ]; then \
	  echo "❌ Lockfile duplicado en $(WEB_DIR)/pnpm-lock.yaml. Usa el lockfile de la raíz."; \
	  exit 1; \
	else \
	  echo "✅ Sin lockfile duplicado en apps/web"; \
	fi
	@if [ ! -f "$(WEB_ENV)" ]; then \
	  echo "⚠️  Falta $(WEB_ENV). Crea uno con:"; \
	  echo "    NEXT_PUBLIC_API_BASE_URL=http://localhost:8000"; \
	  echo "    NEXT_PUBLIC_FEATURE_BULK=1"; \
	else \
	  echo "✅ $(WEB_ENV) encontrado"; \
	fi
	@if [ ! -f "$(WEB_TSCONFIG)" ]; then \
	  echo "❌ Falta $(WEB_TSCONFIG)"; exit 1; \
	fi
	@if ! grep -q '"types"' "$(WEB_TSCONFIG)"; then \
	  echo "⚠️  tsconfig.json no declara \"types\". Añade \"types\": [\"node\"] en compilerOptions."; \
	else \
	  if grep -q '"types":[^]]*node' "$(WEB_TSCONFIG)"; then \
	    echo "✅ tsconfig.json incluye types: node"; \
	  else \
	    echo "⚠️  tsconfig.json no incluye types: node. Añade \"types\": [\"node\"]"; \
	  fi; \
	fi
	@if [ -f "$(WEB_NEXTCONF)" ]; then \
	  echo "✅ next.config.ts encontrado"; \
	else \
	  echo "⚠️  Falta next.config.ts (usando defaults de Next)"; \
	fi
	@echo "🧪 Typecheck..."
	@$(PNPM) -C $(WEB_DIR) typecheck && echo "✅ Typecheck OK" || (echo "❌ Typecheck falló"; exit 1)
