# === Reconciliación de entidades: blocklist + aliases ===
.PHONY: reconcile-all reconcile-blocklist reconcile-aliases reconcile-dry-run reconcile-check prepare-indexes

# Heredadas/por defecto (coherentes con tus otros .mk)
VENV    ?= .venv
PYTHON  ?= $(VENV)/bin/python
PSQL    ?= psql

# DSN por defecto (puedes override al invocar: POSTVERDAD_DSN="...")
POSTVERDAD_DSN ?= dbname=postverdad user=postgres

# Ubicaciones
JOBS_DIR ?= jobs
LOGS_DIR ?= logs
# Runner (si lo tienes en la raíz: invoca con `make ... RUNNER=./reconcile_runner.py`)
RUNNER   ?= $(JOBS_DIR)/reconcile_runner.py

# Flags por defecto del runner
RECON_FLAGS ?= --statement-timeout-ms 60000 --lock-timeout-ms 5000 --max-batches 1000

prepare-indexes: ## Aplica índices idempotentes (una vez)
	@echo "🧱 Aplicando índices (idempotentes)..."
	@$(PSQL) "$$POSTVERDAD_DSN" -v ON_ERROR_STOP=1 -f $(JOBS_DIR)/prepare_indexes.sql
	@echo "✅ Índices aplicados"

reconcile-all: ## Reconciliar blocklist + aliases (logs JSONL)
	@mkdir -p $(LOGS_DIR)
	@echo "♻️  Reconciliando blocklist + aliases..."
	@POSTVERDAD_DSN="$(POSTVERDAD_DSN)" \
	$(PYTHON) $(RUNNER) --only all $(RECON_FLAGS) \
	| tee $(LOGS_DIR)/reconcile_$$(date +%F_%H%M%S).jsonl

reconcile-blocklist: ## Solo blocklist (unlink + prune)
	@mkdir -p $(LOGS_DIR)
	@echo "⛔ Blocklist → unlink + prune..."
	@POSTVERDAD_DSN="$(POSTVERDAD_DSN)" \
	$(PYTHON) $(RUNNER) --only blocklist $(RECON_FLAGS) \
	| tee $(LOGS_DIR)/recon_bl_$$(date +%F_%H%M%S).jsonl

reconcile-aliases: ## Solo aliases (add canonical + delete alias + prune)
	@mkdir -p $(LOGS_DIR)
	@echo "🔗 Aliases → add canonical + delete alias + prune alias entities..."
	@POSTVERDAD_DSN="$(POSTVERDAD_DSN)" \
	$(PYTHON) $(RUNNER) --only aliases $(RECON_FLAGS) \
	| tee $(LOGS_DIR)/recon_al_$$(date +%F_%H%M%S).jsonl

reconcile-dry-run: ## Sin DML; útil para revisar tiempos/locks
	@mkdir -p $(LOGS_DIR)
	@echo "🧪 Dry-run (no DML)..."
	@POSTVERDAD_DSN="$(POSTVERDAD_DSN)" \
	$(PYTHON) $(RUNNER) --only all $(RECON_FLAGS) --dry-run \
	| tee $(LOGS_DIR)/reconcile_dry_$$(date +%F_%H%M%S).jsonl

reconcile-check: ## Verificaciones post-reconcile (conteos)
	@echo "🔎 Verificando estado post-reconcile..."
	@$(PSQL) "$$POSTVERDAD_DSN" -c "SELECT COUNT(*) AS links_bloqueados_restantes FROM articles_entities ae JOIN entities e ON e.id = ae.entity_id JOIN entity_blocklist b ON lower(e.name)=lower(b.term) AND e.type=b.type;"
	@$(PSQL) "$$POSTVERDAD_DSN" -c "SELECT COUNT(*) AS entidades_huerfanas FROM entities e WHERE NOT EXISTS (SELECT 1 FROM articles_entities ae WHERE ae.entity_id = e.id);"
