## Contexto

UI debe comportarse distinto según rol (admin/read).

## Objetivo

Gatear componentes y acciones según rol; usar `RoleBadge` como indicador.

## Cambios incluidos

- Condicionales en botones de edición/bulk
- Mensajes de “sin permisos” cuando corresponda
- (Opcional) Integración posterior con NextAuth; por ahora rol mock/de contexto

## Alcance

- Admin: puede editar/bulk
- Read: sólo lectura

## Acceptance Criteria

- Con rol de lectura, botones de edición no están disponibles/visibles
- Admin ve todo

## Definition of Done

- Sin errores de hidratación
- Doc breve en README (cómo emular roles en dev)

## Cómo probar

- Cambiar rol en `localStorage` o mock y recorrer la UI

## Follow-ups

- Enlazar con NextAuth + RBAC backend

Closes #12
