## Contexto

Offset degrada en datasets grandes. Preferimos cursores para eficiencia.

## Objetivo

Agregar **cursor-based pagination** a `GET /api/articles` y mantener compatibilidad con offset inicialmente.

## Cambios incluidos

- Parámetros `cursor` y `limit`
- Respuesta incluye `next_cursor`
- FE capaz de usar cursor u offset (híbrido)

## Alcance

- Offset sigue disponible (compat)
- Cursor recomendado por defecto

## Acceptance Criteria

- Navegación “Siguiente/Anterior” con cursor funciona
- `limit` respeta 10/20/50

## Definition of Done

- Doc en README-api
- Test manual con límites y múltiples páginas

## Follow-ups

- Índices por `published_at` y `id` para cursores estables

Closes #21
