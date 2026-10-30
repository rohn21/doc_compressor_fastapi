"""Batch compression jobs API endpoints."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Response, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_compression_service, get_db_session, get_storage
from app.core.config import get_settings
from app.database.models import CompressionJob, JobStatus
from app.engines.base import CompressionPreset
from app.schemas.batch import BatchCreate, BatchResponse
from app.schemas.job import JobResponse
from app.services.batch_service import BatchService
from app.services.compression_service import CompressionService
from app.services.storage_service import StorageService

router = APIRouter()
settings = get_settings()


@router.post(
    "/",
    response_model=BatchResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit Batch Compression Operation",
)
async def create_batch_compression(
    files: list[UploadFile],
    preset: Annotated[str, Form()] = CompressionPreset.BALANCED.value,
    target_size: Annotated[str | None, Form()] = None,
    quality: Annotated[int | None, Form()] = None,
    session: Annotated[AsyncSession, Depends(get_db_session)] = None,  # type: ignore[assignment]
    compression_service: Annotated[CompressionService, Depends(get_compression_service)] = None,  # type: ignore[assignment]
) -> BatchResponse:
    """Upload multiple files for batch compression with shared settings."""
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files provided for batch upload",
        )

    if len(files) > settings.MAX_BATCH_FILES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Batch file count ({len(files)}) exceeds maximum limit of "
                f"{settings.MAX_BATCH_FILES}"
            ),
        )

    shared_settings = {
        "preset": preset,
        "target_size": target_size,
        "quality": quality,
    }

    batch = await BatchService.create_batch(
        session,
        BatchCreate(total_files=len(files), shared_settings=shared_settings),
    )

    # Process files
    for file in files:
        content = await file.read()
        filename = file.filename or "upload.bin"
        await compression_service.process_single_file(
            session=session,
            content=content,
            filename=filename,
            preset=preset,
            target_size=target_size,
            quality=quality,
            batch_id=batch.id,
        )

    updated_batch = await BatchService.get_batch(session, batch.id, load_jobs=True)
    assert updated_batch is not None
    return BatchResponse.model_validate(updated_batch)


@router.get(
    "/{batch_id}/",
    response_model=BatchResponse,
    summary="Get Batch Status and Aggregates",
)
async def get_batch_status(
    batch_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)] = None,  # type: ignore[assignment]
) -> BatchResponse:
    """Retrieve aggregate statistics, progress, and status for a batch."""
    batch = await BatchService.get_batch(session, batch_id, load_jobs=True)
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch '{batch_id}' not found",
        )
    return BatchResponse.model_validate(batch)


@router.get(
    "/{batch_id}/files/",
    response_model=list[JobResponse],
    summary="List Individual Files in Batch",
)
async def list_batch_files(
    batch_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)] = None,  # type: ignore[assignment]
) -> list[JobResponse]:
    """List all individual jobs and files belonging to a specific batch."""
    batch = await BatchService.get_batch(session, batch_id)
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch '{batch_id}' not found",
        )

    stmt = (
        select(CompressionJob)
        .where(CompressionJob.batch_id == batch_id)
        .order_by(CompressionJob.created_at)
    )
    result = await session.execute(stmt)
    jobs = result.scalars().all()
    return [JobResponse.model_validate(j) for j in jobs]


@router.get(
    "/{batch_id}/download/",
    summary="Download Batch as ZIP Archive",
)
async def download_batch_archive(
    batch_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)] = None,  # type: ignore[assignment]
    storage: Annotated[StorageService, Depends(get_storage)] = None,  # type: ignore[assignment]
) -> Response:
    """Download all successfully compressed files from a batch as a single ZIP archive."""
    batch = await BatchService.get_batch(session, batch_id, load_jobs=True)
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch '{batch_id}' not found",
        )

    completed_jobs = [
        j for j in batch.jobs if j.status == JobStatus.COMPLETED and j.output_file_reference
    ]

    if not completed_jobs:
        detail_msg = (
            f"No completed files available to download for batch '{batch_id}' "
            f"(Status: {batch.status.value})"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail_msg,
        )

    files_to_zip: list[tuple[str, bytes]] = []
    for job in completed_jobs:
        assert job.output_file_reference is not None
        try:
            content = storage.read_file(job.output_file_reference)
            files_to_zip.append((f"compressed_{job.original_filename}", content))
        except FileNotFoundError:
            continue

    zip_bytes = StorageService.create_zip_archive(files_to_zip)
    zip_filename = f"batch_{str(batch_id)[:8]}.zip"

    headers = {
        "Content-Disposition": f'attachment; filename="{zip_filename}"',
        "Content-Length": str(len(zip_bytes)),
    }

    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers=headers,
    )
