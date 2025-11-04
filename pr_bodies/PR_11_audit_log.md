## Contexto

Necesitamos trazabilidad de cambios (quién, cuándo y qué cambió).

## Objetivo

Crear `audit_log` y helper para registrar cambios en entidades (y futuro artículos).

## Cambios incluidos

- Tabla `audit_log`: `id, actor, action, entity_type, entity_id, before, after, ip, user_agent, created_at`
- Helper en backend para registrar eventos de auditoría
- Integración con endpoints de #9 y #10

## Alcance

- Cobertura mínima: cambios en `entities` (alias/blocked)

## Acceptance Criteria

- Cada cambio genera un evento
- Consultable por fecha/actor/entidad

## Definition of Done

- Documentado el esquema y cómo consultar
- Tests unitarios mínimos del helper

## Cómo probar

- Ejecutar single y bulk y validar entradas en `audit_log`

## Follow-ups

- Exponer `GET /api/audit` con filtros (actor, entity_id, rango)

Closes #11
