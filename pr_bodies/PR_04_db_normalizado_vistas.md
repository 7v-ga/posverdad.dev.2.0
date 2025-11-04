## Contexto

Tenemos `schema.sql` y vistas `v_run_*`. Queremos normalizar nombres, tipos y ofrecer vistas UX-friendly.

## Objetivo

Pulir esquema y añadir `v_fe_articles` consumible por FE.

## Cambios incluidos

- `db/schema.sql`: consistencia de tipos `NUMERIC` vs `REAL`, `NOT NULL` donde aplique
- `v_fe_articles` con columnas: `id,title,url,source,published_at,len_chars,polarity,subjectivity`
- Índices recomendados para filtros y cursores (`published_at`, `(source_id, published_at)`)

## Acceptance Criteria

- `psql -f db/schema.sql` aplica sin errores
- `SELECT * FROM v_fe_articles LIMIT 10` retorna columnas esperadas

## Follow-ups

- Triggers para mantener `articles.len_chars` y hashes

Closes #4
