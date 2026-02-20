import os
import httpx
import trafilatura
from datetime import datetime, timezone
from dateutil import parser
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.schemas import RawArticleCreate
from src.db.models import RawArticle
from src.logger import get_logger

# Set up a logger
logger = get_logger(__name__)

class NewsFetcherService:
    """
    This service is responsible for fetching news articles from external APIs (like NewsAPI),
    extracting the full text using Trafilatura, validating the data with Pydantic, 
    and saving it to the database using SQLAlchemy.
    """
    def __init__(self):
        self.api_key = os.getenv("NEWS_API_KEY")
        if not self.api_key:
            raise ValueError("NEWS_API_KEY is not set in the environment.")
        self.base_url = "https://newsapi.org/v2/everything"

    async def fetch_news_api(self, query: str = "Artificial Intelligence", limit: int = 5) -> list[dict]:
        """Fetches raw JSON from NewsAPI."""
        logger.info(f"Fetching news for query: {query}")
        params = {
            "q": query,
            "language": "en",
            "pageSize": limit,
            "apiKey": self.api_key
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(self.base_url, params=params)
            response.raise_for_status()
            return response.json().get("articles", [])

    def extract_full_text(self, url: str) -> str | None:
        """Uses `trafilatura` to extract the main article body."""
        logger.info(f"Extracting text from: {url}")
        downloaded = trafilatura.fetch_url(url)
        if downloaded is None:
            return None
        return trafilatura.extract(downloaded)

    async def run_ingestion(self, session: AsyncSession, limit: int = 5):
        """The main pipeline: Fetch -> Extract -> Validate -> Save"""
        raw_articles = await self.fetch_news_api(limit=limit)
        
        saved_count = 0
        for article_data in raw_articles:
            # Skip articles that were removed or don't have a URL
            if article_data.get("title") == "[Removed]" or not article_data.get("url"):
                continue

            url = article_data["url"]
            
            # 1. Extract Full Text
            full_text = self.extract_full_text(url)
            
            # 2. Validate Data with Pydantic
            try:
                # We use dateutil.parser because NewsAPI dates can sometimes vary in format
                published_at = parser.parse(article_data["publishedAt"])
                
                validated_data = RawArticleCreate(
                    source_id=article_data["source"].get("id") or article_data["source"].get("name", "unknown"),
                    url=url,
                    title=article_data["title"],
                    published_at=published_at,
                    content=full_text,
                    raw_json=article_data,
                    urlToImage=article_data.get("urlToImage")
                )
            except Exception as e:
                logger.error(f"Validation failed for {url}: {e}")
                continue

            # 3. Save to Database (SQLAlchemy)
            # Check if it already exists to avoid UniqueConstraint errors on the URL
            from sqlalchemy import select
            existing = await session.execute(select(RawArticle).where(RawArticle.url == str(validated_data.url)))
            if existing.scalar_one_or_none():
                logger.info(f"Article already exists in DB, skipping: {url}")
                continue

            new_article = RawArticle(
                source_id=validated_data.source_id,
                url=str(validated_data.url),
                title=validated_data.title,
                content=validated_data.content,
                raw_json=validated_data.raw_json,
                published_at=validated_data.published_at,
                urlToImage=validated_data.urlToImage,
                ingested_at=datetime.now(timezone.utc)
            )
            session.add(new_article)
            saved_count += 1

        # Commit the transaction
        await session.commit()
        logger.info(f"Ingestion complete. Saved {saved_count} new articles to the database.")