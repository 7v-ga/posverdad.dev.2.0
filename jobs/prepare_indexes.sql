-- Índices para escalar blocklist/aliases/joins (idempotentes)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_entities_lower_name_type
  ON entities ((lower(name)), type);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_entity_blocklist_lower_term_type
  ON entity_blocklist ((lower(term)), type);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_entity_aliases_lower_alias_type
  ON entity_aliases ((lower(alias)), type);

ALTER TABLE articles_entities
  ADD CONSTRAINT IF NOT EXISTS uq_articles_entities UNIQUE (article_id, entity_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_articles_entities_entity
  ON articles_entities (entity_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_articles_entities_article
  ON articles_entities (article_id);

CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS uq_articles_url
  ON articles (url);

CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS uq_keywords_word ON keywords (word);
CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS uq_authors_name ON authors (name);
