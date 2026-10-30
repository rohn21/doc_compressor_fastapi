"""Compression jobs API endpoints."""

import mimetypes
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_compression_service, get_db_session, get_storage
from app.engines.base import CompressionPreset
from app.schemas.job import JobResponse
from app.services.compression_service import CompressionService
from app.services.job_service import JobService
from app.services.storage_service import StorageService

router = APIRouter()


@router.post(
    "/jobs/",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit Single Compression Job",
)
async def create_compression_job(
    file: UploadFile,
    preset: Annotated[str, Form()] = CompressionPreset.BALANCED.value,
    target_size: Annotated[str | None, Form()] = None,
    quality: Annotated[int | None, Form()] = None,
    max_dimension: Annotated[int | None, Form()] = None,
    target_format: Annotated[str | None, Form()] = None,
    session: Annotated[AsyncSession, Depends(get_db_session)] = None,  # type: ignore[assignment]
    compression_service: Annotated[CompressionService, Depends(get_compression_service)] = None,  # type: ignore[assignment]
) -> JobResponse:
    """Upload an image or PDF file to compress with preset or target size configurations."""
    content = await file.read()
    filename = file.filename or "upload.bin"

    job = await compression_service.process_single_file(
        session=session,
        content=content,
        filename=filename,
        preset=preset,
        target_size=target_size,
        quality=quality,
        max_dimension=max_dimension,
        target_format=target_format,
    )

    return JobResponse.model_validate(job)


@router.get(
    "/jobs/{job_id}/",
    response_model=JobResponse,
    summary="Get Compression Job Status",
)
async def get_compression_job(
    job_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)] = None,  # type: ignore[assignment]
) -> JobResponse:
    """Retrieve detailed status, statistics, and metadata of a compression job."""
    job = await JobService.get_job(session, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Compression job '{job_id}' not found",
        )
    return JobResponse.model_validate(job)


@router.get(
    "/jobs/{job_id}/download/",
    summary="Download Compressed Output File",
)
async def download_compressed_job(
    job_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)] = None,  # type: ignore[assignment]
    storage: Annotated[StorageService, Depends(get_storage)] = None,  # type: ignore[assignment]
) -> Response:
    """Download the compressed file result for a completed job."""
    job = await JobService.get_job(session, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Compression job '{job_id}' not found",
        )

    if not job.output_file_reference:
        detail_msg = (
            f"Job '{job_id}' has not produced an output file yet (Status: {job.status.value})"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail_msg,
        )

    try:
        content = storage.read_file(job.output_file_reference)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The output file was not found on storage",
        ) from None

    # Guess MIME type
    media_type, _ = mimetypes.guess_type(job.original_filename)
    media_type = media_type or "application/octet-stream"

    filename = f"compressed_{job.original_filename}"
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Content-Length": str(len(content)),
    }

    return Response(content=content, media_type=media_type, headers=headers)
