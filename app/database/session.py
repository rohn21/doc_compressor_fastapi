"""Database engines, session factories, and dependency providers."""

from collections.abc import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.database.base import Base

settings = get_settings()

# Asynchronous engine and session factory (runtime API & services)
async_engine: AsyncEngine = create_async_engine(
    settings.async_database_uri,
    echo=settings.DEBUG,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,
)

async_session_maker: async_sessionmaker[AsyncSession] = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Synchronous engine and session factory (Alembic migrations, offline jobs)
sync_engine = create_engine(
    settings.sync_database_uri,
    echo=settings.DEBUG,
    pool_pre_ping=True,
)

sync_session_maker: sessionmaker[Session] = sessionmaker(
    sync_engine,
    expire_on_commit=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession]:
    """Dependency yielding an asynchronous database session with auto-rollback."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def create_tables(engine: AsyncEngine) -> None:
    """Create all registered database tables (used in tests and standalone runs)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables(engine: AsyncEngine) -> None:
    """Drop all registered database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
