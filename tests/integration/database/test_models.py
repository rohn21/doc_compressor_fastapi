"""Tests for database models, relationships, and computed properties."""

import uuid

import pytest
from app.database.models import (
    BatchCompressionJob,
    BatchStatus,
    CompressionJob,
    JobStatus,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


@pytest.mark.asyncio
async def test_compression_job_persistence(db_session: AsyncSession) -> None:
    job = CompressionJob(
        original_file_reference="storage/raw/test123.jpg",
        original_filename="holiday.jpg",
        original_size=5_000_000,
        file_format="jpeg",
        compression_preset="balanced",
        status=JobStatus.COMPLETED,
        output_file_reference="storage/compressed/test123_compressed.jpg",
        output_size=1_000_000,
        target_achieved=True,
    )
    db_session.add(job)
    await db_session.flush()

    assert isinstance(job.id, uuid.UUID)
    assert job.saved_bytes == 4_000_000
    assert job.saved_percentage == 80.0
    assert job.created_at is not None
    assert job.updated_at is not None

    # Retrieve from database
    stmt = select(CompressionJob).where(CompressionJob.id == job.id)
    res = await db_session.execute(stmt)
    retrieved = res.scalar_one()

    assert retrieved.original_filename == "holiday.jpg"
    assert retrieved.status == JobStatus.COMPLETED
    assert retrieved.output_size == 1_000_000


@pytest.mark.asyncio
async def test_batch_and_jobs_relationship(db_session: AsyncSession) -> None:
    batch = BatchCompressionJob(
        total_files=2,
        shared_settings={"preset": "high_quality"},
        status=BatchStatus.PROCESSING,
    )
    db_session.add(batch)
    await db_session.flush()

    job1 = CompressionJob(
        batch_id=batch.id,
        original_file_reference="storage/raw/file1.png",
        original_filename="file1.png",
        original_size=2_000_000,
        file_format="png",
        status=JobStatus.COMPLETED,
        output_size=1_000_000,
    )
    job2 = CompressionJob(
        batch_id=batch.id,
        original_file_reference="storage/raw/file2.pdf",
        original_filename="file2.pdf",
        original_size=3_000_000,
        file_format="pdf",
        status=JobStatus.COMPLETED,
        output_size=1_500_000,
    )
    db_session.add_all([job1, job2])
    await db_session.flush()

    # Query with selectinload
    stmt = (
        select(BatchCompressionJob)
        .where(BatchCompressionJob.id == batch.id)
        .options(selectinload(BatchCompressionJob.jobs))
    )
    res = await db_session.execute(stmt)
    retrieved_batch = res.scalar_one()

    assert len(retrieved_batch.jobs) == 2
    assert retrieved_batch.jobs[0].original_filename == "file1.png"
    assert retrieved_batch.jobs[1].original_filename == "file2.pdf"
    assert retrieved_batch.jobs[0].batch_id == retrieved_batch.id


@pytest.mark.asyncio
async def test_batch_cascade_delete(db_session: AsyncSession) -> None:
    batch = BatchCompressionJob(total_files=1)
    db_session.add(batch)
    await db_session.flush()

    job = CompressionJob(
        batch_id=batch.id,
        original_file_reference="storage/raw/file.jpg",
        original_filename="file.jpg",
        original_size=1000,
        file_format="jpeg",
    )
    db_session.add(job)
    await db_session.flush()
    job_id = job.id

    # Delete batch
    await db_session.delete(batch)
    await db_session.flush()

    # Verify child job is deleted
    stmt = select(CompressionJob).where(CompressionJob.id == job_id)
    res = await db_session.execute(stmt)
    assert res.scalar_one_or_none() is None
