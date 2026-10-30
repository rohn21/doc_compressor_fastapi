"""Service for managing batch compression operations and status calculations."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models import BatchCompressionJob, BatchStatus, CompressionJob, JobStatus
from app.schemas.batch import BatchCreate


class BatchService:
    """Manages batch orchestration, persistence, and state transitions."""

    @staticmethod
    async def create_batch(
        session: AsyncSession,
        batch_data: BatchCreate,
    ) -> BatchCompressionJob:
        """Create and persist a new batch compression record."""
        batch = BatchCompressionJob(
            shared_settings=batch_data.shared_settings,
            total_files=batch_data.total_files,
            status=BatchStatus.PENDING,
        )
        session.add(batch)
        await session.flush()
        return batch

    @staticmethod
    async def get_batch(
        session: AsyncSession,
        batch_id: uuid.UUID,
        load_jobs: bool = False,
    ) -> BatchCompressionJob | None:
        """Retrieve a batch compression record by UUID, optionally loading related jobs."""
        stmt = select(BatchCompressionJob).where(BatchCompressionJob.id == batch_id)
        if load_jobs:
            stmt = stmt.options(selectinload(BatchCompressionJob.jobs))

        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def recalculate_batch(
        session: AsyncSession,
        batch_id: uuid.UUID,
    ) -> BatchCompressionJob | None:
        """Recalculate batch status, counts, and aggregate file sizes from its jobs."""
        batch = await BatchService.get_batch(session, batch_id, load_jobs=False)
        if not batch:
            return None

        # Query all jobs directly to avoid stale relationship caching in the identity map
        stmt = (
            select(CompressionJob)
            .where(CompressionJob.batch_id == batch_id)
            .order_by(CompressionJob.created_at)
        )
        result = await session.execute(stmt)
        jobs = list(result.scalars().all())

        total = max(batch.total_files or 0, len(jobs))
        completed = sum(1 for j in jobs if j.status == JobStatus.COMPLETED)
        failed = sum(1 for j in jobs if j.status == JobStatus.FAILED)
        processing = sum(1 for j in jobs if j.status == JobStatus.PROCESSING)

        batch.total_files = total
        batch.completed_files = completed
        batch.failed_files = failed

        # Calculate aggregates
        orig_size = sum(j.original_size for j in jobs)
        comp_size = sum(
            j.output_size if j.output_size is not None else j.original_size
            for j in jobs
            if j.status == JobStatus.COMPLETED
        )
        batch.aggregate_original_size = orig_size
        batch.aggregate_compressed_size = comp_size

        # Determine lifecycle status
        if total == 0:
            batch.status = BatchStatus.PENDING
        elif completed == total:
            batch.status = BatchStatus.COMPLETED
            batch.finished_at = batch.finished_at or datetime.now(UTC)
        elif failed == total:
            batch.status = BatchStatus.FAILED
            batch.finished_at = batch.finished_at or datetime.now(UTC)
        elif (completed + failed) == total:
            # All done, mixed outcomes
            batch.status = BatchStatus.PARTIAL
            batch.finished_at = batch.finished_at or datetime.now(UTC)
        elif processing > 0 or (completed + failed) > 0:
            batch.status = BatchStatus.PROCESSING
        else:
            batch.status = BatchStatus.PENDING

        await session.flush()
        # Expire jobs collection on batch instance so any relationship access refreshes
        session.expire(batch, ["jobs"])
        return batch
