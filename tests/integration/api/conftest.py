"""Test fixtures and AsyncClient configuration for API testing."""

from collections.abc import AsyncGenerator
from pathlib import Path

import pytest_asyncio
from app.api.deps import get_db_session, get_storage
from app.main import app
from app.services.storage_service import StorageService
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest_asyncio.fixture
async def api_client(
    db_session: AsyncSession,
    tmp_path: Path,
) -> AsyncGenerator[AsyncClient]:
    """Provide AsyncClient with database and storage dependency overrides."""
    test_storage = StorageService(base_dir=tmp_path / "test_storage")

    async def override_get_db() -> AsyncGenerator[AsyncSession]:
        yield db_session

    def override_get_storage() -> StorageService:
        return test_storage

    app.dependency_overrides[get_db_session] = override_get_db
    app.dependency_overrides[get_storage] = override_get_storage

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client

    app.dependency_overrides.clear()
