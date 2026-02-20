"""
Defines how PostgreSQL stores data and the relationships between tables.
This is the "Model" layer.
"""

from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID, uuid4
from sqlalchemy import String, Text, DateTime, Boolean, Float, ForeignKey, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# The base class for all our database models
class Base(DeclarativeBase):
    pass

# --- Link Table for Many-to-Many Relationship ---
class StorySource(Base):
    __tablename__ = "story_source"
    story_id: Mapped[UUID] = mapped_column(ForeignKey("story.id"), primary_key=True)
    raw_article_id: Mapped[UUID] = mapped_column(ForeignKey("raw_article.id"), primary_key=True)

# --- Table 1: Raw Data ---
class RawArticle(Base):
    __tablename__ = "raw_article"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    source_id: Mapped[str] = mapped_column(String, index=True)
    url: Mapped[str] = mapped_column(String, unique=True, index=True)
    urlToImage: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    title: Mapped[str] = mapped_column(String)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # Trafilatura text
    raw_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    processed: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationship back to stories
    stories: Mapped[List["Story"]] = relationship(secondary="story_source", back_populates="sources")

# --- Table 2: Synthesized AI Stories ---
class Story(Base):
    __tablename__ = "story"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String)
    summary: Mapped[str] = mapped_column(Text)
    sentiment_score: Mapped[float] = mapped_column(Float, default=0.0)
    category: Mapped[str] = mapped_column(String, default="General")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    citation_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Relationship to the raw articles
    sources: Mapped[List["RawArticle"]] = relationship(secondary="story_source", back_populates="stories")