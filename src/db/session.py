"""
Handles database connections and sessions using SQLAlchemy's async capabilities.
This is the "Session" layer, responsible for managing how we interact with the database.
"""

import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from src.db.models import Base

# Load environment variables
load_dotenv()

# Database connection string from environment variables
DATABASE_URL = f"postgresql+asyncpg://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@localhost:5432/{os.getenv('POSTGRES_DB')}"

# Create the async engine
engine = create_async_engine(DATABASE_URL, echo=False, future=True)

# Create a session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# Dependency to inject DB sessions into FastAPI routes and our Services
async def get_session():
    async with AsyncSessionLocal() as session:
        yield session

# Helper to initialize tables
async def init_db():
    async with engine.begin() as conn:
        # Creates tables defined in models.py if they don't exist
        await conn.run_sync(Base.metadata.create_all)