"""Batch compression job database model."""

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, BigInteger, DateTime, Enum, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.database.models.enums import BatchStatus

if TYPE_CHECKING:
    from app.database.models.job import CompressionJob


class BatchCompressionJob(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Represents an aggregate batch compression operation tracking multiple files."""

    __tablename__ = "batch_compression_jobs"

    status: Mapped[BatchStatus] = mapped_column(
        Enum(BatchStatus, name="batch_status_enum", native_enum=False),
        default=BatchStatus.PENDING,
        nullable=False,
        index=True,
    )

    total_files: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_files: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_files: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    shared_settings: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )

    aggregate_original_size: Mapped[int] = mapped_column(
        BigInteger,
        default=0,
        nullable=False,
    )
    aggregate_compressed_size: Mapped[int] = mapped_column(
        BigInteger,
        default=0,
        nullable=False,
    )

    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    jobs: Mapped[list[CompressionJob]] = relationship(
        "CompressionJob",
        back_populates="batch",
        cascade="all, delete-orphan",
        order_by="CompressionJob.created_at",
    )

    def calculate_status(self) -> BatchStatus:
        """Derive batch status based on total, completed, and failed counts."""
        if self.total_files == 0:
            return BatchStatus.PENDING

        processed = self.completed_files + self.failed_files

        if processed < self.total_files:
            return BatchStatus.PROCESSING if processed > 0 else BatchStatus.PENDING

        # All files processed
        if self.completed_files == self.total_files:
            return BatchStatus.COMPLETED

        if self.failed_files == self.total_files:
            return BatchStatus.FAILED

        return BatchStatus.PARTIAL

    @property
    def saved_bytes(self) -> int:
        """Total space saved in bytes."""
        return max(0, self.aggregate_original_size - self.aggregate_compressed_size)

    @property
    def saved_percentage(self) -> float:
        """Overall saved space percentage."""
        if self.aggregate_original_size > 0:
            saved = self.aggregate_original_size - self.aggregate_compressed_size
            return round((saved / self.aggregate_original_size) * 100.0, 2)
        return 0.0
