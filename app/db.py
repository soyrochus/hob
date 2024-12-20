# Copyright © 2025, MIT License, Author: Iwan van der Kleijn 
# Hob: A private AI-augmented workspace for project notes and files.

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite+aiosqlite:///./hob-data.db"

# Create an asynchronous engine
async_engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set True to enable SQL logging
    future=True
)

# Use async session
AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autoflush=False,
    autocommit=False,
    future=True
)

Base = declarative_base()


# Dependency to get a database session
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
