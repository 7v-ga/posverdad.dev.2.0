## Contexto

Ya existe `notify_summary.py`. Formalizarlo con payload consistente y manejo de errores.

## Objetivo

Estandarizar bloques Slack (KPIs + Top fuentes + entidades) y capturar fallos.

## Cambios incluidos

- `scripts/notify_summary.py`: bloqueado por vista `v_run_*`, try/except con fallback
- Formato de mensaje (blocks) estable; enlace a dashboard futuro
- README sección “Notificaciones” (scopes, canal, tokens)

## Acceptance Criteria

- Mensaje con KPIs básicos y top fuentes/entidades
- Manejo de error no rompe pipeline (loggea y continúa)

## Follow-ups

- Adjuntar CSV opcional (gated por token de usuario)

Closes #15
