## Contexto
El filtro `q` ahora hace substring. Migrar a full-text para relevancia.

## Objetivo
Agregar `tsvector` + índice GIN + consulta `plainto_tsquery`/`to_tsquery`.

## Cambios incluidos
- `ALTER TABLE articles ADD COLUMN tsv tsvector;`
- Trigger para mantener `tsv` desde `title` + `body` (config `spanish`)
- Índice GIN sobre `tsv`
- Endpoint API adapta `q` → `WHERE tsv @@ plainto_tsquery('spanish', :q)`

## Acceptance Criteria
- Búsquedas más relevantes
- Explain muestra uso de índice

## Follow-ups
- Rank con `ts_rank_cd` y ordenar por score

Closes #18
