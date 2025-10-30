## Contexto
Asegurar que lo principal no se rompa entre merges.

## Objetivo
Añadir **smoke e2e** con Playwright: carga `/articles`, aplica filtro, exporta CSV.

## Cambios incluidos
- `apps/web/e2e/playwright.config.ts`
- Test `articles.smoke.spec.ts` con:
  - Carga página
  - Escribe en búsqueda (debounce)
  - Verifica tabla con ≥1 fila (cuando haya datos)
  - Exporta CSV y verifica descarga (mock)
- Script `pnpm e2e`

## Acceptance Criteria
- Test corre en local y CI (headless)
- Report básico en artifacts

## Follow-ups
- Añadir casos a11y (#22) y flujo de bulk

Closes #29
