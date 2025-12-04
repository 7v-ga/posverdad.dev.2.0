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
)
from sqlalchemy.orm import declarative_base, relationship

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


class Article(Base):
    __tablename__ = "articles"

    id = Column(BigInteger, primary_key=True, index=True)
    url = Column(Text, nullable=False)
    domain = Column(Text)
    title = Column(Text, nullable=False)
    subtitle = Column(Text)
    body = Column(Text, nullable=False)

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

    source = relationship("Source", back_populates="articles")
    category = relationship("Category", back_populates="articles")
