-- seed_entities_aux.sql
-- Posverdad — Seed inicial para tablas auxiliares de Entities
-- Ejecutar después de crear el esquema (schema.sql).
-- Uso sugerido:
--   psql "$DATABASE_URL" -f seed_entities_aux.sql
-- o
--   python init_db.py --seed   (si tu init lo soporta y el archivo está junto al script)

-- =============================================================
-- 1) Blocklist mínima (términos que no deben guardarse como entidades)
--    *Puedes ampliar/editar esta lista con el tiempo.*
-- =============================================================
INSERT INTO entity_blocklist(term, type_pattern, note) VALUES
  ('además', '.*', 'conector'),
  ('sin embargo', '.*', 'conector'),
  ('no obstante', '.*', 'conector'),
  ('también', '.*', 'adverbio'),
  ('aunque', '.*', 'conector'),
  ('pero', '.*', 'conector'),
  ('asimismo', '.*', 'conector'),
  ('por otra parte', '.*', 'conector'),
  ('por otro lado', '.*', 'conector'),
  ('según', '.*', 'marcador de cita'),
  ('dijo', '.*', 'verbo de reporte'),
  ('señaló', '.*', 'verbo de reporte')
ON CONFLICT (term) DO NOTHING;

-- Sugerencias:
-- - Evita agregar palabras que puedan ser entidades reales en contexto (“Chile”, “Santiago”, etc.).
-- - Si un término ambiguo te genera ruido en un tipo específico, restringe con type_pattern, ej. ('Moneda','LOC','ambigua').

-- =============================================================
-- 2) Aliases de ejemplo (unificación hacia un canónico)
--    *Edita y amplía con tus casos reales.*
--    Estructura general:
--       a) Asegura canónico en entities (name,type)
--       b) Obtén su id
--       c) Inserta alias → canonical_entity_id
-- =============================================================

-- 2.1 Jeanette Jara (PER) ← "Jara"
INSERT INTO entities (name, type) VALUES ('Jeanette Jara', 'PER')
ON CONFLICT (name, type) DO NOTHING;

WITH can AS (
  SELECT id AS canonical_id FROM entities WHERE name='Jeanette Jara' AND type='PER' LIMIT 1
)
INSERT INTO entity_aliases (alias, type, canonical_entity_id, note)
SELECT 'Jara','PER',canonical_id,'Apellido → nombre completo'
FROM can
ON CONFLICT (alias, type) DO NOTHING;

-- 2.2 Gabriel Boric (PER) ← "Boric"
INSERT INTO entities (name, type) VALUES ('Gabriel Boric', 'PER')
ON CONFLICT (name, type) DO NOTHING;

WITH can AS (
  SELECT id AS canonical_id FROM entities WHERE name='Gabriel Boric' AND type='PER' LIMIT 1
)
INSERT INTO entity_aliases (alias, type, canonical_entity_id, note)
SELECT 'Boric','PER',canonical_id,'Apellido → nombre completo'
FROM can
ON CONFLICT (alias, type) DO NOTHING;

-- 2.3 Evelyn Matthei (PER) ← "Matthei"
INSERT INTO entities (name, type) VALUES ('Evelyn Matthei', 'PER')
ON CONFLICT (name, type) DO NOTHING;

WITH can AS (
  SELECT id AS canonical_id FROM entities WHERE name='Evelyn Matthei' AND type='PER' LIMIT 1
)
INSERT INTO entity_aliases (alias, type, canonical_entity_id, note)
SELECT 'Matthei','PER',canonical_id,'Apellido → nombre completo'
FROM can
ON CONFLICT (alias, type) DO NOTHING;

-- 2.4 Carabineros de Chile (ORG) ← "Carabineros"
INSERT INTO entities (name, type) VALUES ('Carabineros de Chile', 'ORG')
ON CONFLICT (name, type) DO NOTHING;

WITH can AS (
  SELECT id AS canonical_id FROM entities WHERE name='Carabineros de Chile' AND type='ORG' LIMIT 1
)
INSERT INTO entity_aliases (alias, type, canonical_entity_id, note)
SELECT 'Carabineros','ORG',canonical_id,'Sigla/forma corta → razón social'
FROM can
ON CONFLICT (alias, type) DO NOTHING;

-- 2.5 Palacio de La Moneda (LOC) ← "La Moneda"
INSERT INTO entities (name, type) VALUES ('Palacio de La Moneda', 'LOC')
ON CONFLICT (name, type) DO NOTHING;

WITH can AS (
  SELECT id AS canonical_id FROM entities WHERE name='Palacio de La Moneda' AND type='LOC' LIMIT 1
)
INSERT INTO entity_aliases (alias, type, canonical_entity_id, note)
SELECT 'La Moneda','LOC',canonical_id,'Topónimo común → forma canónica'
FROM can
ON CONFLICT (alias, type) DO NOTHING;

-- 2.6 Universidad de Chile (ORG) ← "U. de Chile"
INSERT INTO entities (name, type) VALUES ('Universidad de Chile', 'ORG')
ON CONFLICT (name, type) DO NOTHING;

WITH can AS (
  SELECT id AS canonical_id FROM entities WHERE name='Universidad de Chile' AND type='ORG' LIMIT 1
)
INSERT INTO entity_aliases (alias, type, canonical_entity_id, note)
SELECT 'U. de Chile','ORG',canonical_id,'Abreviatura → nombre completo'
FROM can
ON CONFLICT (alias, type) DO NOTHING;

-- 2.7 Ministerio de Salud (ORG) ← "Minsal"
INSERT INTO entities (name, type) VALUES ('Ministerio de Salud', 'ORG')
ON CONFLICT (name, type) DO NOTHING;

WITH can AS (
  SELECT id AS canonical_id FROM entities WHERE name='Ministerio de Salud' AND type='ORG' LIMIT 1
)
INSERT INTO entity_aliases (alias, type, canonical_entity_id, note)
SELECT 'Minsal','ORG',canonical_id,'Sigla → nombre completo'
FROM can
ON CONFLICT (alias, type) DO NOTHING;

-- =============================================================
-- Notas operativas
-- =============================================================
-- • Amplía la blocklist con términos que detectes como ruido en tus corridas.
-- • Para aliases, intenta mantener 1 canónico por entidad y agrega todas sus variantes.
-- • Si una variante puede mapear a más de un canónico (ambigüedad), evita el alias global y
--   deja que lo resuelva la heurística intra-artículo (Apellido→Nombre Apellido cuando exista
--   un único candidato en el mismo texto).
-- • Si te arrepientes de algún alias, bórralo de entity_aliases: las menciones nuevas se insertarán
--   con el (name,type) original; si necesitas actualizar histórico, ejecuta un UPDATE sobre
--   articles_entities para remapear las filas antiguas.
