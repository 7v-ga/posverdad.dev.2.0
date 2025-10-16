WITH targets AS (
  SELECT ae.ctid
  FROM articles_entities ae
  JOIN entities e ON e.id = ae.entity_id
  JOIN entity_aliases a
    ON lower(e.name) = lower(a.alias)
   AND e.type = a.type
  LIMIT 100000
),
del AS (
  DELETE FROM articles_entities ae
  USING targets t
  WHERE ae.ctid = t.ctid
  RETURNING 1
)
SELECT COUNT(*)::bigint AS affected FROM del;
