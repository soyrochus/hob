# Copyright © 2025, MIT License, Author: Iwan van der Kleijn
# Hob: A private AI-augmented workspace for project notes and files.

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from hob.config import SYSTEM, ConfigurationManager as Config

DATABASE_URL = None
async_engine = None
AsyncSessionLocal = None


def init_db():
    # DATABASE_URL = "sqlite+aiosqlite:///./hob-data.db"
    global DATABASE_URL, async_engine, AsyncSessionLocal
    DATABASE_URL = Config.get(SYSTEM, "database-url")

    # Create an asynchronous engine
    async_engine = create_async_engine(
        DATABASE_URL, echo=False, future=True  # Set True to enable SQL logging
    )

    # Use async session
    AsyncSessionLocal = sessionmaker(  # type: ignore
        bind=async_engine,
        class_=AsyncSession,
        autoflush=False,
        autocommit=False,
        future=True,
    )


Base = declarative_base()


# Dependency to get a database session
async def get_db_session():
    global AsyncSessionLocal
    if AsyncSessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    async with AsyncSessionLocal() as session:
        yield session


def get_db_engine():
    if async_engine is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return async_engine
