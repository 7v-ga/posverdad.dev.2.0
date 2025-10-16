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
),
ins AS (
  INSERT INTO articles_entities (article_id, entity_id)
  SELECT article_id, canonical_entity_id FROM to_add
  ON CONFLICT DO NOTHING
  RETURNING 1
)
SELECT COUNT(*)::bigint AS affected FROM ins;
