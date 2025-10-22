## Contexto
Necesitamos una vista rápida para stakeholders.

## Objetivo
Vista `/dashboard` en FE con métricas base desde `v_run_summary` y `v_run_top_sources`.

## Cambios incluidos
- `frontend/src/app/dashboard/page.tsx`: tarjetas KPIs + gráfico simple (Chart.js o Recharts)
- Hook `useDashboardData` con fetch a `/api/runs/summary`
- Skeletons y estados vacíos

## Acceptance Criteria
- KPIs: insertados, descartados, duración, artículos por minuto
- Top fuentes (barra) del último run

## Follow-ups
- Tendencias 30 días y bins de sentimiento

Closes #16
