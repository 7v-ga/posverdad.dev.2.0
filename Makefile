# =============================================================================
# Makefile — Posverdad (raíz)
# =============================================================================
# Convención:
#   - Python: uv + venv local (.venv)
#   - DB: docker compose (servicio: db)
#   - Migraciones: alembic (fuente de verdad del esquema)
#   - Web: pnpm -C apps/web
# =============================================================================

SHELL := /bin/bash
MAKEFLAGS += --no-builtin-rules --no-print-directory

# -----------------------------
# Paths / tooling
# -----------------------------
ROOT_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
VENV_DIR := $(ROOT_DIR)/.venv

PY := $(VENV_DIR)/bin/python
UV := uv

PNPM := pnpm
WEB_DIR := apps/web

COMPOSE := docker compose
DB_SERVICE := db
DB_CONTAINER := posverdad-db-1

# Alembic
ALEMBIC := $(VENV_DIR)/bin/alembic

# -----------------------------
# Pytest
# -----------------------------
PYTEST := $(VENV_DIR)/bin/pytest
# Permite: make test PYTEST_ARGS="..."
PYTEST_ARGS ?=
# Si NO_COV=1, forzamos --no-cov (útil para desarrollo local)
ifeq ($(NO_COV),1)
  PYTEST_ARGS := --no-cov $(PYTEST_ARGS)
endif

# -----------------------------
# Helpers
# -----------------------------
.PHONY: help
help:
	@echo ""
	@echo "Targets:"
	@echo "  make py-install          Instala deps Python (requirements-dev.in) en .venv via uv"
	@echo "  make py-install-prod     Instala deps Python (requirements.in) en .venv via uv"
	@echo "  make py-freeze           Muestra paquetes instalados"
	@echo ""
	@echo "  make db-up               Levanta DB (docker compose up -d db)"
	@echo "  make db-down             Baja servicios"
	@echo "  make db-reset            Baja con -v y sube DB limpia (volúmenes nuevos)"
	@echo "  make db-wait             Espera a que DB esté lista"
	@echo ""
	@echo "  make migrate             Aplica alembic upgrade head"
	@echo "  make migrate-current     Muestra alembic current"
	@echo "  make migrate-revision    Crea revision autogenerate (usa MSG=...)"
	@echo ""
	@echo "  make seed                Ejecuta db/init_db.py (si existe) contra DB actual"
	@echo "  make reset-all           db-reset + migrate + seed"
	@echo ""
	@echo "  make api-dev             Levanta FastAPI (uvicorn apps.api.main:app --reload)"
	@echo "  make web-dev             Levanta Next.js (pnpm -C apps/web dev)"
	@echo "  make web-lint            Lint en apps/web"
	@echo "  make web-typecheck       Typecheck en apps/web"
	@echo ""
	@echo "  make test                Ejecuta pytest (respeta PYTEST_ARGS / NO_COV=1)"
	@echo "  make test-nocov          Ejecuta pytest con --no-cov"
	@echo ""
	@echo "  make scrape              Ejecuta scrapy crawl (SPIDER=..., COUNT=...)"
	@echo ""

# -----------------------------
# Python / env
# -----------------------------
.PHONY: py-install py-install-prod py-freeze
py-install:
	@$(UV) venv $(VENV_DIR) >/dev/null 2>&1 || true
	@$(UV) pip install -r requirements-dev.in

py-install-prod:
	@$(UV) venv $(VENV_DIR) >/dev/null 2>&1 || true
	@$(UV) pip install -r requirements.in

py-freeze:
	@$(PY) -m pip freeze | sort

# -----------------------------
# DB (Docker)
# -----------------------------
.PHONY: db-up db-down db-reset db-wait
db-up:
	@$(COMPOSE) up -d $(DB_SERVICE)

db-down:
	@$(COMPOSE) down

db-reset:
	@$(COMPOSE) down -v
	@$(COMPOSE) up -d $(DB_SERVICE)
	@$(MAKE) db-wait

db-wait:
	@echo "⏳ Esperando Postgres..."
	@until docker exec $(DB_CONTAINER) pg_isready -U posverdad -d posverdad >/dev/null 2>&1; do 	  sleep 1; 	done
	@echo "✅ Postgres listo"

# -----------------------------
# Alembic (migraciones)
# -----------------------------
.PHONY: migrate migrate-current migrate-revision
migrate:
	@$(ALEMBIC) upgrade head

migrate-current:
	@$(ALEMBIC) current

# Uso: make migrate-revision MSG="init"
migrate-revision:
	@if [ -z "$(MSG)" ]; then 	  echo "❌ Debes pasar MSG. Ej: make migrate-revision MSG="init""; 	  exit 1; 	fi
	@$(ALEMBIC) revision --autogenerate -m "$(MSG)"

# -----------------------------
# Seed / reset full
# -----------------------------
.PHONY: seed reset-all
seed:
	@if [ -f "db/init_db.py" ]; then 	  $(PY) db/init_db.py; 	else 	  echo "⚠️  No existe db/init_db.py (seed omitido)"; 	fi

reset-all: db-reset migrate seed
	@echo "✅ reset-all completado"

# -----------------------------
# API / Web
# -----------------------------
.PHONY: api-dev web-dev web-lint web-typecheck
api-dev:
	@$(VENV_DIR)/bin/uvicorn apps.api.main:app --reload --host 0.0.0.0 --port 8000

web-dev:
	@$(PNPM) -C $(WEB_DIR) dev

web-lint:
	@$(PNPM) -C $(WEB_DIR) lint

web-typecheck:
	@$(PNPM) -C $(WEB_DIR) typecheck

# -----------------------------
# Tests
# -----------------------------
.PHONY: test test-nocov
test:
	@command -v $(PYTEST) >/dev/null 2>&1 || ( 	  echo "❌ pytest no está instalado en .venv. Ejecuta: make py-install"; 	  exit 1 	)
	@$(PYTEST) $(PYTEST_ARGS)

test-nocov:
	@$(MAKE) test NO_COV=1

# -----------------------------
# Scrapy
# -----------------------------
# Uso:
#   make scrape SPIDER=el_mostrador COUNT=5
# COUNT es opcional; si se define usa CLOSESPIDER_ITEMCOUNT.
.PHONY: scrape
scrape:
	@if [ -z "$(SPIDER)" ]; then 	  echo "❌ Debes pasar SPIDER. Ej: make scrape SPIDER=el_mostrador COUNT=5"; 	  exit 1; 	fi
	@if [ -n "$(COUNT)" ]; then 	  $(VENV_DIR)/bin/scrapy crawl $(SPIDER) -s CLOSESPIDER_ITEMCOUNT=$(COUNT); 	else 	  $(VENV_DIR)/bin/scrapy crawl $(SPIDER); 	fi