## Contexto

UI necesita editar entidad individual (alias y bloqueo).

## Objetivo

Endpoints de **single edit** con validación y auditoría mínima.

## Cambios incluidos

- `PATCH /api/entities/{id}`: `{ aliasesAdd?: string[], aliasesRemove?: string[], blocked?: boolean }`
- Validación (Pydantic) y reglas básicas
- Registro `audit_log` mínimo

## Alcance

- Acciones unitarias desde dialog de detalle

## Acceptance Criteria

- Cambios persistidos y visibles al recargar
- Auditoría registra el evento

## Definition of Done

- Docs OpenAPI actualizadas
- FE muestra toast de éxito/error

## Cómo probar

- Editar una entidad desde FE
- Ver `audit_log` con el evento

## Follow-ups

- Rate limit básico en endpoints sensibles

Closes #9
