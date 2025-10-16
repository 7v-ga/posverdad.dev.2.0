-- postverdad_views.sql
-- Vistas para clasificar polarity/subjectivity y métricas agregadas
-- No ejecuta nada automáticamente; aplica en tu DB con psql u otro cliente.

-- 1) Vista base con labels/buckets
CREATE OR REPLACE VIEW vw_articles_labeled AS
SELECT
  a.id,
  a.url,
  a.title,
  a.source_id,
  s.name AS source,
  a.publication_date,
  a.polarity,
  a.subjectivity,
  CASE
    WHEN a.polarity IS NULL THEN 'not_calculated'
    WHEN a.polarity = -1     THEN 'negative'
    WHEN a.polarity =  0     THEN 'neutral'
    WHEN a.polarity =  1     THEN 'positive'
    ELSE 'other'
  END AS polarity_label,
  CASE
    WHEN a.subjectivity IS NULL THEN 'not_calculated'
    WHEN a.subjectivity <= 0.15 THEN 'low'     -- 0.00–0.15
    WHEN a.subjectivity <= 0.35 THEN 'medium'  -- 0.16–0.35
    ELSE 'high'                                -- 0.36–1.00
  END AS subjectivity_bucket
FROM articles a
LEFT JOIN sources s ON s.id = a.source_id;

-- 2) Métricas por medio y mes
CREATE OR REPLACE VIEW vw_monthly_media_metrics AS
WITH base AS (
  SELECT
    source,
    date_trunc('month', publication_date::timestamp) AS month,
    polarity_label,
    subjectivity
  FROM vw_articles_labeled
  WHERE publication_date IS NOT NULL
)
SELECT
  source,
  month,
  COUNT(*) AS articles,
  ROUND(100.0 * AVG((polarity_label = 'negative')::int), 1) AS pct_neg,
  ROUND(100.0 * AVG((polarity_label = 'neutral')::int), 1)  AS pct_neu,
  ROUND(100.0 * AVG((polarity_label = 'positive')::int), 1) AS pct_pos,
  ROUND(AVG(subjectivity)::numeric, 3) AS avg_subjectivity,
  ROUND(100.0 * AVG( (subjectivity IS NOT NULL AND subjectivity >= 0.36)::int ), 1) AS pct_high_subjectivity
FROM base
GROUP BY source, month;

-- 3) Matriz polarity × subjectivity_bucket últimos 30 días
CREATE OR REPLACE VIEW vw_last30_polarity_subjectivity_matrix AS
SELECT
  CASE
    WHEN polarity IS NULL THEN 'not_calc'
    WHEN polarity = -1 THEN 'neg'
    WHEN polarity =  0 THEN 'neu'
    WHEN polarity =  1 THEN 'pos'
    ELSE 'other'
  END AS pol,
  CASE
    WHEN subjectivity IS NULL THEN 'not_calc'
    WHEN subjectivity <= 0.15 THEN 'low'
    WHEN subjectivity <= 0.35 THEN 'medium'
    ELSE 'high'
  END AS subj_bin,
  COUNT(*) AS n
FROM articles
WHERE publication_date >= (CURRENT_DATE - INTERVAL '30 days')
GROUP BY 1,2
ORDER BY 1,2;
