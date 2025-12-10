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
from sqlalchemy.orm import declarative_base, relationship, column_property
from sqlalchemy.dialects.postgresql import JSONB

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

  id = Column(BigInteger, primary_key=True, index=True)
  url = Column(Text, nullable=False)
  domain = Column(Text)
  title = Column(Text, nullable=False)
  subtitle = Column(Text)
  body = Column(Text, nullable=False)

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

  # 🔢 Longitud calculada del cuerpo (no es columna física)
  len_chars = column_property(func.length(body))


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
