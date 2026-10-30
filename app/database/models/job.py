"""Individual compression job database model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.database.models.enums import JobStatus

if TYPE_CHECKING:
    from app.database.models.batch import BatchCompressionJob


class CompressionJob(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Tracks a single file compression operation and its lifecycle."""

    __tablename__ = "compression_jobs"

    batch_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("batch_compression_jobs.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    original_file_reference: Mapped[str] = mapped_column(
        String(1024),
        nullable=False,
    )
    output_file_reference: Mapped[str | None] = mapped_column(
        String(1024),
        nullable=True,
    )
    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    original_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    output_size: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    file_format: Mapped[str] = mapped_column(String(32), nullable=False, index=True)

    compression_preset: Mapped[str | None] = mapped_column(String(64), nullable=True)
    target_size: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="job_status_enum", native_enum=False),
        default=JobStatus.PENDING,
        nullable=False,
        index=True,
    )

    target_achieved: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    warning_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    job_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )

    # Relationships
    batch: Mapped[BatchCompressionJob | None] = relationship(
        "BatchCompressionJob",
        back_populates="jobs",
    )

    @property
    def saved_bytes(self) -> int:
        """Space saved in bytes."""
        if self.output_size is not None:
            return max(0, self.original_size - self.output_size)
        return 0

    @property
    def saved_percentage(self) -> float:
        """Percentage of space saved."""
        if self.original_size > 0 and self.output_size is not None:
            saved = self.original_size - self.output_size
            return round((saved / self.original_size) * 100.0, 2)
        return 0.0
