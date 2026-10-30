"""FastAPI dependency providers."""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_async_session
from app.services.compression_service import CompressionService
from app.services.storage_service import StorageService, get_storage_service


async def get_db_session() -> AsyncGenerator[AsyncSession]:
    """Provide transactional database session."""
    async for session in get_async_session():
        yield session


def get_storage() -> StorageService:
    """Provide storage service instance."""
    return get_storage_service()


def get_compression_service(
    storage: Annotated[StorageService, Depends(get_storage)],
) -> CompressionService:
    """Provide compression service instance."""
    return CompressionService(storage=storage)
