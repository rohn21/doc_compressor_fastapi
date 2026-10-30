"""Tests for batch compression REST endpoints and ZIP packaging."""

import io
import zipfile

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_batch_compression_and_zip_download(
    api_client: AsyncClient,
    sample_rgb_bytes: bytes,
    sample_text_pdf_bytes: bytes,
) -> None:
    # 1. POST /api/v1/batches/
    files = [
        ("files", ("photo.jpg", sample_rgb_bytes, "image/jpeg")),
        ("files", ("document.pdf", sample_text_pdf_bytes, "application/pdf")),
    ]
    data = {"preset": "balanced"}

    response = await api_client.post("/api/v1/batches/", files=files, data=data)
    assert response.status_code == 201
    batch = response.json()

    batch_id = batch["id"]
    assert batch["total_files"] == 2
    assert batch["completed_files"] == 2
    assert batch["status"] == "COMPLETED"
    assert batch["aggregate_original_size"] > 0
    assert batch["aggregate_compressed_size"] > 0

    # 2. GET /api/v1/batches/{batch_id}/
    get_res = await api_client.get(f"/api/v1/batches/{batch_id}/")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == batch_id

    # 3. GET /api/v1/batches/{batch_id}/files/
    files_res = await api_client.get(f"/api/v1/batches/{batch_id}/files/")
    assert files_res.status_code == 200
    job_list = files_res.json()
    assert len(job_list) == 2
    filenames = [j["original_filename"] for j in job_list]
    assert "photo.jpg" in filenames
    assert "document.pdf" in filenames

    # 4. GET /api/v1/batches/{batch_id}/download/
    dl_res = await api_client.get(f"/api/v1/batches/{batch_id}/download/")
    assert dl_res.status_code == 200
    assert dl_res.headers.get("content-type") == "application/zip"

    # Verify ZIP integrity and files
    with zipfile.ZipFile(io.BytesIO(dl_res.content), "r") as z:
        names = z.namelist()
        assert len(names) == 2
        assert any("photo" in n for n in names)
        assert any("document" in n for n in names)
