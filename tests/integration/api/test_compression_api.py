"""Tests for single-file compression REST endpoints."""

import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_compress_image_flow(
    api_client: AsyncClient,
    sample_rgb_bytes: bytes,
) -> None:
    # 1. POST /api/v1/compression/jobs/
    files = {"file": ("sample.jpg", sample_rgb_bytes, "image/jpeg")}
    data = {"preset": "balanced"}

    response = await api_client.post("/api/v1/compression/jobs/", files=files, data=data)
    assert response.status_code == 201
    job = response.json()

    assert job["id"] is not None
    job_id = job["id"]
    assert job["status"] == "COMPLETED"
    assert job["original_filename"] == "sample.jpg"
    assert job["file_format"] == "jpeg"
    assert job["output_size"] is not None
    assert job["output_size"] > 0

    # 2. GET /api/v1/compression/jobs/{job_id}/
    get_res = await api_client.get(f"/api/v1/compression/jobs/{job_id}/")
    assert get_res.status_code == 200
    retrieved = get_res.json()
    assert retrieved["id"] == job_id
    assert retrieved["status"] == "COMPLETED"

    # 3. GET /api/v1/compression/jobs/{job_id}/download/
    dl_res = await api_client.get(f"/api/v1/compression/jobs/{job_id}/download/")
    assert dl_res.status_code == 200
    assert "attachment" in dl_res.headers.get("content-disposition", "")
    assert len(dl_res.content) == job["output_size"]


@pytest.mark.asyncio
async def test_compress_pdf_flow(
    api_client: AsyncClient,
    sample_text_pdf_bytes: bytes,
) -> None:
    files = {"file": ("report.pdf", sample_text_pdf_bytes, "application/pdf")}
    data = {"preset": "high_quality"}

    response = await api_client.post("/api/v1/compression/jobs/", files=files, data=data)
    assert response.status_code == 201
    job = response.json()

    assert job["status"] == "COMPLETED"
    assert job["file_format"] == "pdf"
    assert job["output_size"] is not None


@pytest.mark.asyncio
async def test_get_nonexistent_job(api_client: AsyncClient) -> None:
    random_id = uuid.uuid4()
    response = await api_client.get(f"/api/v1/compression/jobs/{random_id}/")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
