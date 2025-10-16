# === Notificaciones y reportes a Slack ===
.PHONY: notify-test notify-last notify-run _require-slack

# Heredadas de env.mk
VENV    ?= .venv
PYTHON  ?= $(VENV)/bin/python

# Si usas webhook o bot, valida que exista al menos una credencial y un canal
_require-slack:
	@if [ -z "$${SLACK_WEBHOOK_URL:-}" ] && [ -z "$${SLACK_BOT_TOKEN:-}" ]; then \
		echo "❌ SLACK_WEBHOOK_URL o SLACK_BOT_TOKEN no definidos en tu entorno/.env"; \
		echo "   Ejemplo: SLACK_BOT_TOKEN=xoxb-...  o  SLACK_WEBHOOK_URL=https://hooks.slack.com/services/..."; \
		exit 1; \
	fi
	@if [ -z "$${SLACK_CHANNEL:-}" ]; then \
		echo "❌ SLACK_CHANNEL no definido (ID C…/G… o #nombre)"; \
		exit 1; \
	fi

notify-test: _require-slack ## Enviar prueba de notificación a Slack
	@echo "🚨 Enviando test de notificación a Slack..."
	@$(PYTHON) scripts/notify_test.py

notify-last: clean-graphs _require-slack ## Notificar última corrida a Slack (desde DB)
	@echo "🔔 Notificando última corrida en Slack (desde DB)..."
	@RUN_ID=$$(PGPASSWORD=$$POSTGRES_PASSWORD psql -h $${POSTGRES_HOST:-localhost} -U $$POSTGRES_USER -d $$POSTGRES_DB -Atc \
	 "SELECT run_id FROM nlp_runs ORDER BY COALESCE(started_at, date) DESC NULLS LAST LIMIT 1;"); \
	if [ -z "$$RUN_ID" ]; then echo "❌ No hay corridas en nlp_runs"; exit 1; fi; \
	echo "🆔 $$RUN_ID"; \
	$(PYTHON) scripts/notify_summary.py --run-id $$RUN_ID

notify-run: clean-graphs _require-slack ## Notificar una corrida específica: make notify-run RUN_ID=2025...
	@RUN_ID="$${RUN_ID}"; \
	if [ -z "$$RUN_ID" ]; then echo "❌ Debes pasar RUN_ID=... (ej: make notify-run RUN_ID=20251010-122729-ae2efc7a)"; exit 1; fi; \
	echo "🔔 Notificando corrida $$RUN_ID en Slack..."; \
	$(PYTHON) scripts/notify_summary.py --run-id $$RUN_ID
