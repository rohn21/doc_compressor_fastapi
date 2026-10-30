"""Status enumerations for compression jobs and batches."""

from enum import StrEnum


class JobStatus(StrEnum):
    """Lifecycle states of an individual compression job."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class BatchStatus(StrEnum):
    """Lifecycle states of a batch compression operation."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
