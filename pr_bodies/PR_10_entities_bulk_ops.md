## Contexto

Se requieren operaciones masivas desde la selección de la tabla.

## Objetivo

Endpoints bulk para `blocked` y `aliases`.

## Cambios incluidos

- `POST /api/entities/blocked` → `{ ids: number[], blocked: boolean }`
- `POST /api/entities/alias` → `{ ids: number[], alias: string }`
- Auditoría por cada entidad (o registro consolidado)

## Alcance

- FE integra barra de acciones masivas (ya mock) con la API real

## Acceptance Criteria

- Afecta correctamente N entidades seleccionadas
- Feedback visual y rehidratación del estado

## Definition of Done

- Docs OpenAPI actualizadas
- Validaciones (ids no vacíos, alias no vacío, etc.)

## Cómo probar

- Seleccionar 3–5 entidades, bloquear/alias
- Revisar auditoría

## Follow-ups

- Dry-run opcional

Closes #10
