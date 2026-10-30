"""Service for managing individual compression jobs."""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import CompressionJob, JobStatus
from app.schemas.job import JobCreate, JobUpdate


class JobService:
    """Manages compression job lifecycle and persistence."""

    @staticmethod
    async def create_job(
        session: AsyncSession,
        job_data: JobCreate,
    ) -> CompressionJob:
        """Create and persist a new compression job."""
        job = CompressionJob(
            batch_id=job_data.batch_id,
            original_file_reference=job_data.original_file_reference,
            original_filename=job_data.original_filename,
            original_size=job_data.original_size,
            file_format=job_data.file_format,
            compression_preset=job_data.compression_preset,
            target_size=job_data.target_size,
            job_metadata=job_data.job_metadata,
            status=JobStatus.PENDING,
        )
        session.add(job)
        await session.flush()
        return job

    @staticmethod
    async def get_job(
        session: AsyncSession,
        job_id: uuid.UUID,
    ) -> CompressionJob | None:
        """Retrieve a compression job by its UUID."""
        stmt = select(CompressionJob).where(CompressionJob.id == job_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_job(
        session: AsyncSession,
        job_id: uuid.UUID,
        update_data: JobUpdate,
    ) -> CompressionJob | None:
        """Update an existing job's status and properties."""
        job = await JobService.get_job(session, job_id)
        if not job:
            return None

        for field, value in update_data.model_dump(exclude_unset=True).items():
            setattr(job, field, value)

        await session.flush()
        return job

    @staticmethod
    async def mark_completed(
        session: AsyncSession,
        job_id: uuid.UUID,
        output_file_reference: str,
        output_size: int,
        target_achieved: bool | None = None,
        warning_message: str | None = None,
        metadata_update: dict[str, Any] | None = None,
    ) -> CompressionJob | None:
        """Mark a job as successfully COMPLETED."""
        job = await JobService.get_job(session, job_id)
        if not job:
            return None

        job.status = JobStatus.COMPLETED
        job.output_file_reference = output_file_reference
        job.output_size = output_size
        job.target_achieved = target_achieved
        job.warning_message = warning_message
        job.finished_at = datetime.now(UTC)

        if metadata_update:
            job.job_metadata = {**job.job_metadata, **metadata_update}

        await session.flush()
        return job

    @staticmethod
    async def mark_failed(
        session: AsyncSession,
        job_id: uuid.UUID,
        error_message: str,
    ) -> CompressionJob | None:
        """Mark a job as FAILED with an error message."""
        job = await JobService.get_job(session, job_id)
        if not job:
            return None

        job.status = JobStatus.FAILED
        job.error_message = error_message
        job.finished_at = datetime.now(UTC)
        await session.flush()
        return job
