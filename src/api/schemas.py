"""
Defines the data structures used for API requests and responses.
This is the "Schema" layer, which serves as a contract for how data should look when it enters or leaves the system.
"""

from pydantic import BaseModel, HttpUrl, ConfigDict, Field
from datetime import datetime
from typing import Optional, List
from uuid import UUID

# --- Raw Article Schemas ---
class RawArticleBase(BaseModel):
    source_id: str
    url: HttpUrl
    urlToImage: Optional[HttpUrl] = None
    title: str
    published_at: datetime

# Used when fetching from NewsAPI and inserting into the DB
class RawArticleCreate(RawArticleBase):
    content: Optional[str] = None
    raw_json: Optional[dict] = None
    urlToImage: Optional[str] = None

# Used when sending data to the LangGraph Agents or API responses
class RawArticleRead(RawArticleBase):
    id: UUID
    content: Optional[str] = None
    ingested_at: datetime
    processed: bool
    
    # This tells Pydantic it can read data directly from SQLAlchemy objects
    model_config = ConfigDict(from_attributes=True) 

# --- Story Schemas ---
class StoryBase(BaseModel):
    title: str
    summary: str
    sentiment_score: float = Field(default=0.0)
    category: str = Field(default="General")
    citation_verified: bool = Field(default=False)

# What the LangGraph Publisher Agent will output
class StoryCreate(StoryBase):
    source_article_ids: List[UUID]

# What the End User sees when they hit the FastAPI /feed endpoint
class StoryRead(StoryBase):
    id: UUID
    created_at: datetime
    sources: List[RawArticleRead] = []
    
    model_config = ConfigDict(from_attributes=True)