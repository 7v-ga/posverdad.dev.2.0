WITH targets AS (
  SELECT ae.ctid
  FROM articles_entities ae
  JOIN entities e ON e.id = ae.entity_id
  JOIN entity_blocklist b
    ON lower(e.name) = lower(b.term)
   AND e.type = b.type
  LIMIT 100000
),
del AS (
  DELETE FROM articles_entities ae
  USING targets t
  WHERE ae.ctid = t.ctid
  RETURNING 1
)
SELECT COUNT(*)::bigint AS affected FROM del;
