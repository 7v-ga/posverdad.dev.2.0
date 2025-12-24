# apps/api/models.py
from datetime import datetime, date

from sqlalchemy import (
    BigInteger,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    Text,
    Table,
    func,
)
from sqlalchemy import Boolean, JSON, String, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship, column_property
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

Base = declarative_base()


class Source(Base):
  __tablename__ = "sources"

  id = Column(Integer, primary_key=True, index=True)
  name = Column(Text, nullable=False)
  domain = Column(Text)

  articles = relationship("Article", back_populates="source")


class Category(Base):
  __tablename__ = "categories"

  id = Column(Integer, primary_key=True, index=True)
  name = Column(Text, nullable=False)

  articles = relationship("Article", back_populates="category")


# Tabla de asociación artículos ↔ entidades (N:M)
articles_entities = Table(
  "articles_entities",
  Base.metadata,
  Column("article_id", BigInteger, ForeignKey("articles.id"), primary_key=True),
  Column("entity_id", Integer, ForeignKey("entities.id"), primary_key=True),
  Column("salience", Numeric),
)


class Article(Base):
  __tablename__ = "articles"
  __table_args__ = (
    UniqueConstraint("url", name="uq_articles_url"),
  )

  id = Column(BigInteger, primary_key=True, index=True)
  url = Column(Text, nullable=False)
  domain = Column(Text)
  title = Column(Text, nullable=False)
  subtitle = Column(Text)
  body = Column(Text, nullable=False)
  len_chars = Column(Integer, nullable=False)

  body_hash = Column(Text)
  hash = Column(Text)

  source_id = Column(Integer, ForeignKey("sources.id"))
  category_id = Column(Integer, ForeignKey("categories.id"))

  publication_date = Column(Date)
  published_at = Column(DateTime)
  scraped_at = Column(DateTime)

  polarity = Column(Numeric)
  subjectivity = Column(Numeric)
  language = Column(Text)

  meta_description = Column(Text)
  meta_keywords = Column(Text)
  image = Column(Text)
  run_id = Column(Text)

  # JSONB con datos NLP (entities crudas, framing, etc.)
  preprocessed_data = Column(JSONB, default=dict)

  source = relationship("Source", back_populates="articles")
  category = relationship("Category", back_populates="articles")

  # Entidades normalizadas (N:M)
  entities = relationship(
    "Entity",
    secondary="articles_entities",
    back_populates="articles",
  )


class Entity(Base):
  __tablename__ = "entities"

  id = Column(Integer, primary_key=True, index=True)
  name = Column(Text, nullable=False)
  type = Column(Text)  # PER, ORG, LOC, MISC, etc.

  # Relación inversa a artículos
  articles = relationship(
    "Article",
    secondary="articles_entities",
    back_populates="entities",
  )

class EntityMention(Base):
    __tablename__ = "entity_mentions"

    id = Column(BigInteger, primary_key=True, index=True)
    article_id = Column(BigInteger, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False)

    raw_text = Column(Text, nullable=False)
    raw_label = Column(Text)

    span_start = Column(Integer)
    span_end = Column(Integer)

    canonical_entity_id = Column(Integer, ForeignKey("entities.id", ondelete="SET NULL"), nullable=True)

    status = Column(Text, nullable=False, default="PENDING")
    decision_scope = Column(Text, nullable=False, default="UNDECIDED")

    note = Column(Text)
    reviewed_by = Column(Text)
    reviewed_at = Column(DateTime)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    article = relationship("Article", backref="entity_mentions")
    canonical_entity = relationship("Entity", foreign_keys=[canonical_entity_id])


class EntityAction(Base):
    __tablename__ = "entity_actions"

    id = Column(BigInteger, primary_key=True, index=True)
    action_type = Column(Text, nullable=False)
    scope = Column(Text, nullable=False)
    status = Column(Text, nullable=False, default="APPLIED")
    payload = Column(JSONB, nullable=False, default=dict)

    created_by = Column(Text)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)