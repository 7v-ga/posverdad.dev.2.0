## Contexto

Extender el dashboard básico con vistas analíticas.

## Objetivo

3 paneles: cohortes por semana, histograma de polaridad/subjectividad, NER por fuente.

## Cambios incluidos

- Endpoints: `/api/runs/series`, `/api/runs/sentiment_bins`, `/api/runs/entities_top`
- FE: `/dashboard/analytics` con 3 charts y filtros (fecha/fuente)
- Caching leve (in-memory) para endpoints

## Acceptance Criteria

- Visualizaciones interactivas
- Tooltips + leyendas claras

## Follow-ups

- Exportar gráficos a PNG/CSV

Closes #23
