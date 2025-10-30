## Contexto
Se requiere un indicador visual y reutilizable de rol de usuario (admin/read) para usar en tablas, topbar y vistas de detalle.

## Objetivo
Crear `RoleBadge` (admin/read) accesible y consistente con el theming (shadcn/ui).

## Cambios incluidos
- `apps/web/src/components/RoleBadge.tsx` (nuevo)
- Ejemplo de uso integrado en un punto visible de la UI (topbar o tabla)

## Alcance
- Render de “admin” (énfasis) o “lectura” (neutro)
- Accesible: contraste AA

## Acceptance Criteria
- Texto correcto según el rol
- Sin roturas en light/dark
- Tipado estricto (TS)

## Definition of Done
- `pnpm typecheck` y `pnpm dev` sin errores
- Screenshot en el PR (opcional)
- README actualizado si aplica

## Cómo probar
- Insertar `<RoleBadge role="admin" />` y `<RoleBadge role="read" />` en un componente visible
- Verificar estilos y accesibilidad

## Follow-ups
- Usarlo en pantallas de usuarios/permisos

Closes #30
