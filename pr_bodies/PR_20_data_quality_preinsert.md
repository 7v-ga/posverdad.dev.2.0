## Contexto

Evitar basura en DB: URL vacías, títulos nulos, fechas inconsistentes.

## Objetivo

Validar antes de persistir en pipeline y, opcionalmente, constraints suaves.

## Cambios incluidos

- Validaciones en `pipelines.py`/storage layer (Python)
- Reglas: URL no vacía, título no vacío, `published_at` razonable, idioma conocido
- Métrica `discarded_invalid` incrementada

## Acceptance Criteria

- Inserts inválidos se registran como descartados
- Logs apuntan motivo concreto

## Follow-ups

- Reporte de calidad por run

Closes #20
