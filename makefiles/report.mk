# === Exportación de runs y reportes ===
.PHONY: summary-local export-last-run runs-report check-vacios

# Heredadas de env.mk
VENV    ?= .venv
PYTHON  ?= $(VENV)/bin/python

# Directorios estándar (puedes ajustarlos o tomarlos de .env si tus scripts lo hacen)
REPORTS_DIR ?= reports
GRAPHS_DIR  ?= graphs

# Helper: verificar que exista .last_run (sin depender de notify.mk)
CHECK_LAST_RUN = if [ ! -f .last_run ]; then \
	echo "❌ Archivo .last_run no encontrado. Ejecuta primero 'make scrape'"; \
	exit 1; \
fi

summary-local: clean-graphs ## Generar resumen local del último run (sin Slack)
	@$(CHECK_LAST_RUN)
	@mkdir -p $(REPORTS_DIR) $(GRAPHS_DIR)
	@echo "📊 Generando resumen local (LAST_RUN_ID=$$(cat .last_run))..."
	@export LAST_RUN_ID=$$(cat .last_run); \
	$(PYTHON) scripts/report_summary.py

export-last-run: ## Exportar artículos del último run a JSON
	@$(CHECK_LAST_RUN)
	@mkdir -p $(REPORTS_DIR)
	@echo "📄 Exportando artículos del último run (LAST_RUN_ID=$$(cat .last_run))..."
	@export LAST_RUN_ID=$$(cat .last_run); \
	$(PYTHON) scripts/export_last_run.py

runs-report: ## Generar reporte histórico de runs (usa ARGS="--desde 2025-08-01" p.ej.)
	@echo "📈 Ejecutando reporte de runs... $(ARGS)"
	@$(PYTHON) scripts/report_runs.py $(ARGS)

check-vacios: ## Detectar runs vacíos recientes (últimos 3 días)
	@echo "🔎 Verificando si hay runs vacíos recientes (últimos 3 días)..."
	@$(PYTHON) scripts/check_vacios.py
