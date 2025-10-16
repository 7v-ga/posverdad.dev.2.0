WITH targets AS (
  SELECT e.ctid
  FROM entities e
  WHERE NOT EXISTS (
    SELECT 1 FROM articles_entities ae WHERE ae.entity_id = e.id
  )
    AND EXISTS (
      SELECT 1
      FROM entity_aliases a
      WHERE lower(e.name) = lower(a.alias)
        AND e.type = a.type
    )
  LIMIT 100000
),
del AS (
  DELETE FROM entities e
  USING targets t
  WHERE e.ctid = t.ctid
  RETURNING 1
)
SELECT COUNT(*)::bigint AS affected FROM del;
