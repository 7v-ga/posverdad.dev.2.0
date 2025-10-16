-- 1) Desenlazar vínculos de entidades bloqueadas (batches)
WITH blocked_links AS (
  SELECT ae.ctid
  FROM articles_entities ae
  JOIN entities e ON e.id = ae.entity_id
  JOIN entity_blocklist b
    ON lower(e.name) = lower(b.term)
   AND e.type = b.type
  LIMIT 100000
)
DELETE FROM articles_entities ae
USING blocked_links bl
WHERE ae.ctid = bl.ctid;

-- Repetir hasta 0 filas afectadas.

-- 2) Podar entidades huérfanas (batches)
WITH orphans AS (
  SELECT e.ctid
  FROM entities e
  WHERE NOT EXISTS (SELECT 1 FROM articles_entities ae WHERE ae.entity_id = e.id)
  LIMIT 100000
)
DELETE FROM entities e
USING orphans o
WHERE e.ctid = o.ctid;

-- Repetir hasta 0 filas afectadas.
