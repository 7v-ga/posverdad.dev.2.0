## Contexto
Necesitamos entender performance y fallos.

## Objetivo
Logging JSON, métricas Prometheus y tracing básico (OTel).

## Cambios incluidos
- Logging estructurado en API y jobs (uvicorn/structlog)
- Endpoint `/metrics` (Prometheus)
- OpenTelemetry SDK con exporter sencillo (stdout u OTLP)

## Acceptance Criteria
- Logs parseables (fields: level, msg, path, duration)
- `/metrics` expone contadores/latencias

## Follow-ups
- Jaeger/Tempo para tracing en dev

Closes #27
