"""Tests for health check API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check_endpoint(api_client: AsyncClient) -> None:
    response = await api_client.get("/api/v1/health/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert data["database"] == "connected"


@pytest.mark.asyncio
async def test_root_redirect(api_client: AsyncClient) -> None:
    response = await api_client.get("/", follow_redirects=False)
    assert response.status_code in (307, 302)
    assert response.headers["location"] == "/docs"
