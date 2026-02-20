import asyncio
from dotenv import load_dotenv
from src.db.session import init_db, AsyncSessionLocal
from src.services.news_fetcher import NewsFetcherService

# Load environment variables
load_dotenv()

async def main():
    print("🚀 Bootstrapping Sentinel AI News MVP...")
    
    # 1. Initialize the Database Tables
    print("📦 Creating database tables...")
    await init_db()
    
    # 2. Run the Ingestion Pipeline
    print("📰 Starting Ingestion Service...")
    fetcher = NewsFetcherService()
    
    async with AsyncSessionLocal() as session:
        # Let's fetch 5 articles for our initial test
        await fetcher.run_ingestion(session=session, limit=5)
        
    print("✅ Bootstrap complete! Check your database.")

if __name__ == "__main__":
    asyncio.run(main())