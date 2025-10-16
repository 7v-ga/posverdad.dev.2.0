-- 1) Añadir vínculos canónicos faltantes (evitar duplicados)
WITH to_add AS (
  SELECT DISTINCT ae.article_id, a.canonical_entity_id
  FROM articles_entities ae
  JOIN entities e ON e.id = ae.entity_id
  JOIN entity_aliases a
    ON lower(e.name) = lower(a.alias)
   AND e.type = a.type
  LEFT JOIN articles_entities ae2
    ON ae2.article_id = ae.article_id
   AND ae2.entity_id = a.canonical_entity_id
  WHERE ae2.article_id IS NULL
  LIMIT 100000
)
INSERT INTO articles_entities (article_id, entity_id)
SELECT article_id, canonical_entity_id FROM to_add
ON CONFLICT DO NOTHING;

-- 2) Eliminar vínculos antiguos hacia alias (batches)
WITH to_del AS (
  SELECT ae.ctid
  FROM articles_entities ae
  JOIN entities e ON e.id = ae.entity_id
  JOIN entity_aliases a
    ON lower(e.name) = lower(a.alias)
   AND e.type = a.type
  LIMIT 100000
)
DELETE FROM articles_entities ae
USING to_del d
WHERE ae.ctid = d.ctid;

-- 3) Podar entidades alias huérfanas (batches)
WITH orphans AS (
  SELECT e.ctid
  FROM entities e
  WHERE NOT EXISTS (SELECT 1 FROM articles_entities ae WHERE ae.entity_id = e.id)
    AND EXISTS (
      SELECT 1 FROM entity_aliases a
      WHERE lower(e.name) = lower(a.alias)
        AND e.type = a.type
    )
  LIMIT 100000
)
DELETE FROM entities e
USING orphans o
WHERE e.ctid = o.ctid;

-- Repetir cada bloque hasta 0 filas afectadas.
