"""Tests for error handling, validation, and HTTP status codes in API."""

import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_upload_empty_file_returns_400(api_client: AsyncClient) -> None:
    files = {"file": ("empty.jpg", b"", "image/jpeg")}
    response = await api_client.post("/api/v1/compression/jobs/", files=files)
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert "empty" in data["detail"].lower()


@pytest.mark.asyncio
async def test_upload_unsupported_format_returns_415(api_client: AsyncClient) -> None:
    garbage = b"not-an-image-or-pdf-garbage-payload-123456789"
    files = {"file": ("unknown.xyz", garbage, "application/octet-stream")}
    response = await api_client.post("/api/v1/compression/jobs/", files=files)
    assert response.status_code == 415
    data = response.json()
    assert data["error"] == "UnsupportedFormatError"


@pytest.mark.asyncio
async def test_batch_download_nonexistent_returns_404(api_client: AsyncClient) -> None:
    random_batch = uuid.uuid4()
    response = await api_client.get(f"/api/v1/batches/{random_batch}/download/")
    assert response.status_code == 404
