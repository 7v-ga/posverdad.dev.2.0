-- postverdad_entities_packC_queries.sql
-- Rango parametrizable: :start, :end (usa placeholders %(start)s, %(end)s en tu cliente)
-- Filtrado opcional por tipos (IN) y medios (sources.name)

-- Base: artículos × entidades en rango
SELECT
  a.id   AS article_id,
  a.publication_date,
  a.polarity,
  a.subjectivity,
  s.name AS source,
  e.id   AS entity_id,
  e.name AS entity_name,
  e.type AS entity_type
FROM articles a
JOIN articles_entities ae ON ae.article_id = a.id
JOIN entities e ON e.id = ae.entity_id
LEFT JOIN sources s ON s.id = a.source_id
WHERE a.publication_date >= %(start)s
  AND a.publication_date < (%(end)s::date + INTERVAL '1 day');

-- Perfil: fuentes top para una entidad
SELECT s.name AS source, COUNT(*) AS n
FROM articles a
JOIN articles_entities ae ON ae.article_id = a.id
JOIN entities e ON e.id = ae.entity_id
LEFT JOIN sources s ON s.id = a.source_id
WHERE a.publication_date >= %(start)s
  AND a.publication_date < (%(end)s::date + INTERVAL '1 day')
  AND e.name = %(entity)s
GROUP BY s.name
ORDER BY n DESC
LIMIT 10;

-- Perfil: timeline diario de una entidad
SELECT date_trunc('day', a.publication_date::timestamp) AS period, COUNT(*) AS n
FROM articles a
JOIN articles_entities ae ON ae.article_id = a.id
JOIN entities e ON e.id = ae.entity_id
WHERE a.publication_date >= %(start)s
  AND a.publication_date < (%(end)s::date + INTERVAL '1 day')
  AND e.name = %(entity)s
GROUP BY period
ORDER BY period;

-- Perfil: distribución de polarity por entidad (%)
SELECT
  ROUND(100.0 * AVG((a.polarity = -1)::int), 1) AS pct_neg,
  ROUND(100.0 * AVG((a.polarity =  0)::int), 1) AS pct_neu,
  ROUND(100.0 * AVG((a.polarity =  1)::int), 1) AS pct_pos,
  ROUND(AVG(a.polarity)::numeric, 3)            AS avg_polarity
FROM articles a
JOIN articles_entities ae ON ae.article_id = a.id
JOIN entities e ON e.id = ae.entity_id
WHERE a.publication_date >= %(start)s
  AND a.publication_date < (%(end)s::date + INTERVAL '1 day')
  AND e.name = %(entity)s;

-- Perfil: subjectivity (media y cuantiles)
-- (Cuantiles exactos conviene calcularlos en pandas; en SQL puedes aproximar con percentiles_cont)
SELECT
  AVG(a.subjectivity) AS avg_subjectivity
FROM articles a
JOIN articles_entities ae ON ae.article_id = a.id
JOIN entities e ON e.id = ae.entity_id
WHERE a.publication_date >= %(start)s
  AND a.publication_date < (%(end)s::date + INTERVAL '1 day')
  AND e.name = %(entity)s;

-- Perfil: co-ocurrencias con otras entidades
SELECT e2.name AS other_entity, COUNT(DISTINCT a.id) AS n
FROM articles a
JOIN articles_entities ae1 ON ae1.article_id = a.id
JOIN entities e1 ON e1.id = ae1.entity_id
JOIN articles_entities ae2 ON ae2.article_id = a.id AND ae2.entity_id <> ae1.entity_id
JOIN entities e2 ON e2.id = ae2.entity_id
WHERE a.publication_date >= %(start)s
  AND a.publication_date < (%(end)s::date + INTERVAL '1 day')
  AND e1.name = %(entity)s
GROUP BY e2.name
ORDER BY n DESC
LIMIT 20;

-- (1 reducido) Top Entities
SELECT e.name AS entity_name, e.type AS entity_type, COUNT(*) AS n
FROM articles a
JOIN articles_entities ae ON ae.article_id = a.id
JOIN entities e ON e.id = ae.entity_id
LEFT JOIN sources s ON s.id = a.source_id
WHERE a.publication_date >= %(start)s
  AND a.publication_date < (%(end)s::date + INTERVAL '1 day')
GROUP BY e.name, e.type
ORDER BY n DESC
LIMIT 20;

-- (2 reducido) Tendencias para un conjunto de entidades (diario)
SELECT e.name AS entity_name,
       date_trunc('day', a.publication_date::timestamp) AS period,
       COUNT(*) AS n
FROM articles a
JOIN articles_entities ae ON ae.article_id = a.id
JOIN entities e ON e.id = ae.entity_id
WHERE a.publication_date >= %(start)s
  AND a.publication_date < (%(end)s::date + INTERVAL '1 day')
  AND e.name = ANY(%(entities)s)
GROUP BY e.name, period
ORDER BY e.name, period;
