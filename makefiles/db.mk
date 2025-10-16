# === Base de datos y servicios (Docker Compose) ===
# Archivo: makefiles/db.mk

.PHONY: status-db init-db init-db-reset \
        compose-up compose-down compose-reset compose-pull \
        db-up db-down db-nuke db-shell db-logs \
        db-backup db-restore db-restore-safe db-psql-file db-port db-seed

# --- Variables heredadas / defaults ---
VENV              ?= .venv
PYTHON            ?= $(VENV)/bin/python

COMPOSE_FILE      ?= docker-compose.yml
DB_SERVICE    ?= db
REDIS_SERVICE ?= redis
SEED_FILE     ?= seed_entities_aux.sql

# Parámetros de espera (puedes sobreescribirlos al invocar make)
WAIT_DB_TIMEOUT   ?= 60          # segundos totales de espera
WAIT_DB_INTERVAL  ?= 1           # segundos entre reintentos

# Backups
BACKUP_DIR        ?= backups
BACKUP_PREFIX     ?= postverdad
# Nombre de archivo: backups/postverdad-20250101-235959.sql.gz
BACKUP_FILE       = $(BACKUP_DIR)/$(BACKUP_PREFIX)-$$(date +%Y%m%d-%H%M%S).sql.gz

# --- Helpers ---
# (El target 'wait-db' se ha eliminado: Compose --wait + smoke test cubren la espera)

# --- Python scripts ---

status-db: ## Verificar base de datos y tablas mediante script Python
	@echo "🔍 Verificando base de datos y tablas..."
	@$(PYTHON) scripts/check_db.py

init-db: ## Crear/actualizar el esquema de la DB (no destructivo)
	@$(PYTHON) db/init_db.py

init-db-reset: ## Resetear DB (drop + create + schema) - ⚠️ DESTRUCTIVO
	@$(PYTHON) db/init_db.py --reset -y

# --- Docker Compose ---

compose-up: ## Levantar servicios (Postgres + Redis) y esperar healthchecks
	@echo "📦 Levantando servicios con docker compose (con --wait)..."
	@docker compose -f $(COMPOSE_FILE) up -d --wait

compose-down: ## Bajar servicios (sin borrar volúmenes)
	@echo "🛑 Bajando servicios (sin borrar volúmenes)..."
	@docker compose -f $(COMPOSE_FILE) down

compose-reset: ## Bajar servicios y BORRAR volúmenes - ⚠️ DESTRUCTIVO
	@echo "🧨 Borrando servicios y volúmenes (destructivo)..."
	@docker compose -f $(COMPOSE_FILE) down -v

compose-pull: ## Actualizar imágenes (pull)
	@echo "📥 Descargando imágenes actualizadas..."
	@docker compose -f $(COMPOSE_FILE) pull

# --- Aliases de conveniencia ---

# Tiempo máximo del smoke test (segundos) para pg_isready
WAIT_DB_SMOKE_TIMEOUT ?= 15

db-up: compose-up ## Levantar DB/Redis y verificar que Postgres acepta conexiones (smoke test)
	@echo "🔎 Smoke test de Postgres (pg_isready, timeout $(WAIT_DB_SMOKE_TIMEOUT)s)..."
	@deadline=$$(( $$(date +%s) + $(WAIT_DB_SMOKE_TIMEOUT) )); \
	while true; do \
	  if docker compose -f $(COMPOSE_FILE) exec -T $(DB_SERVICE) \
	    pg_isready -U "$${POSTGRES_USER:-postverdad}" -d "$${POSTGRES_DB:-postverdad}" >/dev/null 2>&1; then \
	    echo "✅ Postgres listo (accepting connections)"; break; \
	  fi; \
	  [ $$(date +%s) -ge $$deadline ] && { echo "❌ Timeout en smoke test de pg_isready"; exit 1; }; \
	  sleep 1; \
	done

db-down: compose-down ## Bajar DB/Redis (conserva volúmenes)

db-nuke: compose-reset ## Destruye contenedores y volúmenes (DESTRUCTIVO)

db-shell: ## Abrir psql dentro del servicio de Postgres
	@docker compose -f $(COMPOSE_FILE) exec $(DB_SERVICE) \
		psql -U "$${POSTGRES_USER:-postverdad}" -d "$${POSTGRES_DB:-postverdad}"

db-logs: ## Ver logs en vivo de Postgres
	@docker compose -f $(COMPOSE_FILE) logs -f $(DB_SERVICE)

# --- Backups / Restore ---

db-backup: ## Crea backup comprimido del esquema+datos (pg_dump | gzip) en $(BACKUP_DIR)
	@mkdir -p "$(BACKUP_DIR)"
	@echo "💾 Creando backup en $(BACKUP_DIR)..."
	@set -o pipefail; \
	docker compose -f $(COMPOSE_FILE) exec -T $(DB_SERVICE) \
		sh -ceu 'pg_dump -U "$${POSTGRES_USER:-postverdad}" -d "$${POSTGRES_DB:-postverdad}" -F p --no-owner --no-privileges' \
	| gzip > "$(BACKUP_FILE)"
	@ls -lh "$(BACKUP_DIR)" | tail -n 1
	@echo "✅ Backup creado: $$(ls -1t $(BACKUP_DIR) | head -n1)"

db-restore: ## Restaura backup .sql(.gz) sobrescribiendo esquema (DROP SCHEMA public CASCADE). Uso: make db-restore FILE=backups/xxx.sql.gz
ifndef FILE
	$(error Debes pasar FILE= ruta al backup .sql o .sql.gz)
endif
	@echo "🧩 Restaurando desde $(FILE) (modo destructivo del esquema public)..."
	@docker compose -f $(COMPOSE_FILE) exec -T $(DB_SERVICE) \
		sh -ceu 'psql -U "$${POSTGRES_USER:-postverdad}" -d "$${POSTGRES_DB:-postverdad}" -v ON_ERROR_STOP=1 -c "DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public;"'
	@if echo "$(FILE)" | grep -qi '\.gz$$'; then \
		gunzip -c "$(FILE)" | docker compose -f $(COMPOSE_FILE) exec -T $(DB_SERVICE) \
			psql -U "$${POSTGRES_USER:-postverdad}" -d "$${POSTGRES_DB:-postverdad}" -v ON_ERROR_STOP=1 ; \
	else \
		cat "$(FILE)" | docker compose -f $(COMPOSE_FILE) exec -T $(DB_SERVICE) \
			psql -U "$${POSTGRES_USER:-postverdad}" -d "$${POSTGRES_DB:-postverdad}" -v ON_ERROR_STOP=1 ; \
	fi
	@echo "✅ Restore completado"

db-restore-safe: ## Restaura SIN dropear esquema (aplica sobre tablas existentes). Uso: make db-restore-safe FILE=...
ifndef FILE
	$(error Debes pasar FILE= ruta al backup .sql o .sql.gz)
endif
	@echo "🧩 Restaurando (modo seguro, sin DROP SCHEMA) desde $(FILE)..."
	@if echo "$(FILE)" | grep -qi '\.gz$$'; then \
		gunzip -c "$(FILE)" | docker compose -f $(COMPOSE_FILE) exec -T $(DB_SERVICE) \
			psql -U "$${POSTGRES_USER:-postverdad}" -d "$${POSTGRES_DB:-postverdad}" -v ON_ERROR_STOP=1 ; \
	else \
		cat "$(FILE)" | docker compose -f $(COMPOSE_FILE) exec -T $(DB_SERVICE) \
			psql -U "$${POSTGRES_USER:-postverdad}" -d "$${POSTGRES_DB:-postverdad}" -v ON_ERROR_STOP=1 ; \
	fi
	@echo "✅ Restore seguro completado"

db-psql-file: ## Ejecuta un archivo SQL arbitrario contra la DB. Uso: make db-psql-file FILE=script.sql
ifndef FILE
	$(error Debes pasar FILE= ruta al archivo .sql)
endif
	@echo "📜 Ejecutando SQL: $(FILE)"
	@cat "$(FILE)" | docker compose -f $(COMPOSE_FILE) exec -T $(DB_SERVICE) \
		psql -U "$${POSTGRES_USER:-postverdad}" -d "$${POSTGRES_DB:-postverdad}" -v ON_ERROR_STOP=1
	@echo "✅ SQL ejecutado"

db-port: ## Muestra quién usa el puerto de Postgres en el host
	@echo "🔎 Puerto Postgres host: $${POSTGRES_PORT:-5432}"
	@docker ps --format "table {{.ID}}\t{{.Names}}\t{{.Ports}}" \
	| grep -E "0\.0\.0\.0:$${POSTGRES_PORT:-5432}|:::$${POSTGRES_PORT:-5432}" || true

# --- Seed de Entities (blocklist + aliases) ---
db-seed: ## Cargar seed de entidades. Usa SEED_FILE=... si cambias la ruta
	@if [ ! -f "$(SEED_FILE)" ]; then \
	  echo "❌ No encuentro $(SEED_FILE). Pasa SEED_FILE=... o colócalo en la raíz del repo."; \
	  exit 1; \
	fi
	@$(MAKE) -s db-psql-file FILE="$(SEED_FILE)"
	@echo "🌱 Seed aplicado: $(SEED_FILE)"
