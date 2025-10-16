-- ===============================================
-- Posverdad — schema.sql (NORMALIZADO + REPORTING)
-- ===============================================

-- ===============================================
-- Corridas / metadatos del pipeline
-- ===============================================
CREATE TABLE IF NOT EXISTS nlp_runs (
    run_id                 TEXT PRIMARY KEY,
    date                   TIMESTAMPTZ DEFAULT NOW(),
    started_at             TIMESTAMPTZ,
    finished_at            TIMESTAMPTZ,
    status                 TEXT,
    notes                  TEXT,
    total_inserted         INTEGER DEFAULT 0,
    total_discarded        INTEGER DEFAULT 0,
    total_updated          INTEGER DEFAULT 0,
    total_errors           INTEGER DEFAULT 0,
    duration_seconds       INTEGER,
    -- Contadores precisos (D)
    discarded_duplicates   INTEGER DEFAULT 0,
    discarded_invalid      INTEGER DEFAULT 0
);

-- ===============================================
-- Fuentes / catálogos base
-- ===============================================
CREATE TABLE IF NOT EXISTS sources (
    id        SERIAL PRIMARY KEY,
    name      TEXT NOT NULL,
    domain    TEXT,
    UNIQUE (domain)
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_sources_name ON sources (name);

CREATE TABLE IF NOT EXISTS authors (
    id        SERIAL PRIMARY KEY,
    name      TEXT NOT NULL,
    UNIQUE (name)
);

CREATE TABLE IF NOT EXISTS categories (
    id        SERIAL PRIMARY KEY,
    name      TEXT NOT NULL,
    UNIQUE (name)
);

CREATE TABLE IF NOT EXISTS keywords (
    id        SERIAL PRIMARY KEY,
    word      TEXT NOT NULL,
    UNIQUE (word)
);

CREATE TABLE IF NOT EXISTS entities (
    id        SERIAL PRIMARY KEY,
    name      TEXT NOT NULL,
    type      TEXT,
    UNIQUE (name, type)
);
CREATE INDEX IF NOT EXISTS idx_entities_name_type ON entities(name, type);

-- ===============================================
-- Artículos
-- ===============================================
CREATE TABLE IF NOT EXISTS articles (
    id                BIGSERIAL PRIMARY KEY,
    url               TEXT NOT NULL,
    domain            TEXT,
    title             TEXT NOT NULL,
    subtitle          TEXT,
    body              TEXT NOT NULL,

    body_hash         TEXT,
    hash              TEXT,

    source_id         INTEGER REFERENCES sources(id)    ON DELETE SET NULL,
    category_id       INTEGER REFERENCES categories(id) ON DELETE SET NULL,

    publication_date  DATE,
    published_at      TIMESTAMPTZ,

    scraped_at        TIMESTAMPTZ DEFAULT NOW(),
    run_id            TEXT REFERENCES nlp_runs(run_id)  ON DELETE SET NULL,

    preprocessed_data JSONB DEFAULT '{}'::jsonb,

    image             TEXT,
    meta_description  TEXT,
    meta_keywords     TEXT,

    polarity          NUMERIC,
    subjectivity      NUMERIC,
    language          TEXT
);

-- Unicidad por URL (idempotencia por URL canónica)
CREATE UNIQUE INDEX IF NOT EXISTS uq_articles_url           ON articles((url));

-- Índices útiles
CREATE INDEX       IF NOT EXISTS idx_articles_run_id        ON articles(run_id);
CREATE INDEX       IF NOT EXISTS idx_articles_pubdate       ON articles(publication_date);
CREATE INDEX       IF NOT EXISTS idx_articles_published_at  ON articles(published_at);
CREATE INDEX       IF NOT EXISTS idx_articles_preproc_gin   ON articles USING GIN (preprocessed_data);

-- ===============================================
-- Relaciones N:M
-- ===============================================
CREATE TABLE IF NOT EXISTS articles_authors (
    article_id  BIGINT  REFERENCES articles(id) ON DELETE CASCADE,
    author_id   INTEGER REFERENCES authors(id)  ON DELETE CASCADE,
    PRIMARY KEY (article_id, author_id)
);

CREATE TABLE IF NOT EXISTS articles_keywords (
    article_id  BIGINT  REFERENCES articles(id) ON DELETE CASCADE,
    keyword_id  INTEGER REFERENCES keywords(id) ON DELETE CASCADE,
    PRIMARY KEY (article_id, keyword_id)
);

CREATE TABLE IF NOT EXISTS articles_entities (
    article_id  BIGINT  REFERENCES articles(id) ON DELETE CASCADE,
    entity_id   INTEGER REFERENCES entities(id) ON DELETE CASCADE,
    salience    NUMERIC,
    PRIMARY KEY (article_id, entity_id)
);

-- Relación N:M artículos ↔ categorías (multi-categoría)
CREATE TABLE IF NOT EXISTS articles_categories (
    article_id  BIGINT  REFERENCES articles(id)   ON DELETE CASCADE,
    category_id INTEGER REFERENCES categories(id) ON DELETE CASCADE,
    PRIMARY KEY (article_id, category_id)
);
CREATE INDEX IF NOT EXISTS idx_articles_categories_article  ON articles_categories(article_id);
CREATE INDEX IF NOT EXISTS idx_articles_categories_category ON articles_categories(category_id);

-- ===============================================
-- Framing por artículo (1:1)
-- ===============================================
CREATE TABLE IF NOT EXISTS framings (
    id                BIGSERIAL PRIMARY KEY,
    article_id        BIGINT REFERENCES articles(id) ON DELETE CASCADE,
    ideological_frame TEXT,
    actors            TEXT[],
    victims           TEXT[],
    antagonists       TEXT[],
    emotions          TEXT[],
    summary           TEXT
);
-- Asegurar 1:1 (un framing por artículo)
DROP INDEX IF EXISTS idx_framings_article_id;
CREATE UNIQUE INDEX IF NOT EXISTS ux_framings_article_id ON framings(article_id);

-- ===============================================
-- Aliases & Blocklist de entidades
-- ===============================================
CREATE TABLE IF NOT EXISTS entity_aliases (
  alias TEXT NOT NULL,
  type  TEXT NOT NULL,
  canonical_entity_id INTEGER NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
  note TEXT,
  PRIMARY KEY (alias, type)
);
CREATE INDEX IF NOT EXISTS idx_entity_aliases_canonical ON entity_aliases(canonical_entity_id);

-- Blocklist: términos que nunca deben guardarse como entidades
CREATE TABLE IF NOT EXISTS entity_blocklist (
  term TEXT PRIMARY KEY,
  type_pattern TEXT DEFAULT '.*', -- regex (PER|ORG|LOC|MISC|...)
  note TEXT
);

-- ===============================================
-- Correcciones/normalizaciones y constraints adicionales
-- ===============================================

-- Normaliza dominios vacíos a NULL para no colisionar con UNIQUE(domain)
UPDATE sources SET domain = NULL WHERE domain = '';

-- ===============================================
-- ====== VISTAS DE REPORTING (para Slack/analítica) ======
-- ===============================================

-- Resumen por run: KPIs, longitudes y promedios de sentimiento
CREATE OR REPLACE VIEW v_run_summary AS
WITH base AS (
  SELECT
    r.run_id,
    r.started_at,
    r.finished_at,
    COALESCE(NULLIF(r.duration_seconds, 0),
             EXTRACT(EPOCH FROM (r.finished_at - r.started_at))::int) AS duration_seconds,
    r.total_inserted,
    r.total_discarded,
    r.total_updated,
    r.total_errors,
    r.discarded_duplicates,
    r.discarded_invalid
  FROM nlp_runs r
),
agg AS (
  SELECT
    a.run_id,
    COUNT(*)                         AS articles_count,
    COUNT(DISTINCT COALESCE(a.source_id::TEXT, a.domain)) AS sources_count,
    AVG(LENGTH(a.body))::NUMERIC     AS avg_len_chars,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY LENGTH(a.body))::NUMERIC AS p50_len_chars,
    AVG(a.polarity)::NUMERIC         AS avg_polarity,
    AVG(a.subjectivity)::NUMERIC     AS avg_subjectivity
  FROM articles a
  GROUP BY a.run_id
)
SELECT
  b.run_id,
  b.duration_seconds,
  b.total_inserted,
  b.total_discarded,
  b.total_updated,
  b.total_errors,
  b.discarded_duplicates,
  b.discarded_invalid,
  COALESCE(ag.articles_count, 0)     AS articles_count,
  COALESCE(ag.sources_count, 0)      AS sources_count,
  ag.avg_len_chars,
  ag.p50_len_chars,
  ag.avg_polarity,
  ag.avg_subjectivity,
  CASE
    WHEN b.duration_seconds IS NOT NULL AND b.duration_seconds > 0
    THEN ROUND((b.total_inserted::NUMERIC / b.duration_seconds) * 60.0, 2)
    ELSE NULL
  END AS items_per_minute
FROM base b
LEFT JOIN agg ag ON ag.run_id = b.run_id;

-- Top fuentes por run (nombre de source si existe, si no, dominio)
CREATE OR REPLACE VIEW v_run_top_sources AS
SELECT
  a.run_id,
  COALESCE(s.name, NULLIF(a.domain,''), 'unknown') AS source_name,
  COUNT(*)::INT AS articles
FROM articles a
LEFT JOIN sources s ON s.id = a.source_id
GROUP BY a.run_id, COALESCE(s.name, NULLIF(a.domain,''), 'unknown');

-- Top entidades por run (todas las types; el consumidor puede filtrar)
CREATE OR REPLACE VIEW v_run_entities_top AS
SELECT
  a.run_id,
  e.name           AS entity_name,
  e.type           AS entity_type,
  COUNT(*)::INT    AS mentions
FROM articles_entities ae
JOIN articles a ON a.id = ae.article_id
JOIN entities e ON e.id = ae.entity_id
GROUP BY a.run_id, e.name, e.type;

-- Binning de sentimiento (polarity y subjectivity) por run
CREATE OR REPLACE VIEW v_run_sentiment_bins AS
WITH pol AS (
  SELECT
    a.run_id,
    CASE
      WHEN a.polarity IS NULL        THEN 'unknown'
      WHEN a.polarity < -0.6         THEN 'very_negative'
      WHEN a.polarity < -0.2         THEN 'negative'
      WHEN a.polarity <= 0.2         THEN 'neutral'
      WHEN a.polarity <= 0.6         THEN 'positive'
      ELSE 'very_positive'
    END AS bucket,
    COUNT(*)::INT AS n
  FROM articles a
  GROUP BY 1, 2
),
subj AS (
  SELECT
    a.run_id,
    CASE
      WHEN a.subjectivity IS NULL    THEN 'unknown'
      WHEN a.subjectivity < 0.33     THEN 'low'
      WHEN a.subjectivity < 0.66     THEN 'medium'
      ELSE 'high'
    END AS bucket,
    COUNT(*)::INT AS n
  FROM articles a
  GROUP BY 1, 2
)
SELECT 'polarity'::TEXT AS metric, run_id, bucket, n FROM pol
UNION ALL
SELECT 'subjectivity'::TEXT, run_id, bucket, n FROM subj;

-- Top artículos por run (score = |polarity| + subjectivity + ln(len+1))
CREATE OR REPLACE VIEW v_run_top_articles AS
SELECT
  a.run_id,
  a.id,
  a.title,
  a.url,
  a.domain,
  LENGTH(a.body)::INT                      AS len_chars,
  a.polarity,
  a.subjectivity,
  (COALESCE(ABS(a.polarity),0) + COALESCE(a.subjectivity,0)
    + LN(GREATEST(LENGTH(a.body),0)+1))    AS score
FROM articles a;

-- ===============================================
-- Fin de schema.sql
-- ===============================================
