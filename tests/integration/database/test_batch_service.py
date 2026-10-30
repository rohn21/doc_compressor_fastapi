"""Tests for BatchService and JobService state calculation and aggregation."""

import pytest
from app.database.models import BatchStatus
from app.schemas.batch import BatchCreate
from app.schemas.job import JobCreate
from app.services.batch_service import BatchService
from app.services.job_service import JobService
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_batch_all_completed_calculation(db_session: AsyncSession) -> None:
    batch = await BatchService.create_batch(
        db_session,
        BatchCreate(total_files=2, shared_settings={"preset": "balanced"}),
    )

    # Add 2 jobs
    job1 = await JobService.create_job(
        db_session,
        JobCreate(
            batch_id=batch.id,
            original_file_reference="storage/img1.jpg",
            original_filename="img1.jpg",
            original_size=10_000,
            file_format="jpeg",
        ),
    )
    job2 = await JobService.create_job(
        db_session,
        JobCreate(
            batch_id=batch.id,
            original_file_reference="storage/img2.jpg",
            original_filename="img2.jpg",
            original_size=20_000,
            file_format="jpeg",
        ),
    )

    # Initial recalculation: both pending
    recalc = await BatchService.recalculate_batch(db_session, batch.id)
    assert recalc is not None
    assert recalc.status == BatchStatus.PENDING

    # Mark job1 completed
    await JobService.mark_completed(
        db_session,
        job1.id,
        output_file_reference="storage/out1.jpg",
        output_size=4_000,
    )
    recalc = await BatchService.recalculate_batch(db_session, batch.id)
    assert recalc is not None
    assert recalc.status == BatchStatus.PROCESSING
    assert recalc.completed_files == 1

    # Mark job2 completed
    await JobService.mark_completed(
        db_session,
        job2.id,
        output_file_reference="storage/out2.jpg",
        output_size=6_000,
    )
    recalc = await BatchService.recalculate_batch(db_session, batch.id)
    assert recalc is not None
    assert recalc.status == BatchStatus.COMPLETED
    assert recalc.completed_files == 2
    assert recalc.failed_files == 0
    assert recalc.aggregate_original_size == 30_000
    assert recalc.aggregate_compressed_size == 10_000
    assert recalc.saved_bytes == 20_000
    assert recalc.saved_percentage == 66.67
    assert recalc.finished_at is not None


@pytest.mark.asyncio
async def test_batch_partial_failure_calculation(db_session: AsyncSession) -> None:
    batch = await BatchService.create_batch(
        db_session,
        BatchCreate(total_files=2),
    )

    job1 = await JobService.create_job(
        db_session,
        JobCreate(
            batch_id=batch.id,
            original_file_reference="storage/doc.pdf",
            original_filename="doc.pdf",
            original_size=50_000,
            file_format="pdf",
        ),
    )
    job2 = await JobService.create_job(
        db_session,
        JobCreate(
            batch_id=batch.id,
            original_file_reference="storage/corrupt.png",
            original_filename="corrupt.png",
            original_size=10_000,
            file_format="png",
        ),
    )

    # Mark job1 as completed
    await JobService.mark_completed(
        db_session,
        job1.id,
        output_file_reference="storage/out.pdf",
        output_size=25_000,
    )

    # Mark job2 as failed
    await JobService.mark_failed(
        db_session,
        job2.id,
        error_message="Image data corrupted",
    )

    recalc = await BatchService.recalculate_batch(db_session, batch.id)
    assert recalc is not None
    assert recalc.status == BatchStatus.PARTIAL
    assert recalc.completed_files == 1
    assert recalc.failed_files == 1
    assert recalc.finished_at is not None


@pytest.mark.asyncio
async def test_batch_all_failed_calculation(db_session: AsyncSession) -> None:
    batch = await BatchService.create_batch(
        db_session,
        BatchCreate(total_files=1),
    )

    job = await JobService.create_job(
        db_session,
        JobCreate(
            batch_id=batch.id,
            original_file_reference="storage/enc.pdf",
            original_filename="enc.pdf",
            original_size=5_000,
            file_format="pdf",
        ),
    )

    await JobService.mark_failed(
        db_session,
        job.id,
        error_message="PDF password required",
    )

    recalc = await BatchService.recalculate_batch(db_session, batch.id)
    assert recalc is not None
    assert recalc.status == BatchStatus.FAILED
    assert recalc.completed_files == 0
    assert recalc.failed_files == 1
    assert recalc.finished_at is not None
