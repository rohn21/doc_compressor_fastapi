"""Pydantic schemas for batch compression jobs."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.database.models.enums import BatchStatus
from app.schemas.job import JobResponse


class BatchCreate(BaseModel):
    """Schema for initializing a batch compression job."""

    shared_settings: dict[str, Any] = Field(default_factory=dict)
    total_files: int = Field(ge=0, default=0)


class BatchResponse(BaseModel):
    """Schema for returning batch compression state and aggregates."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: BatchStatus
    total_files: int
    completed_files: int
    failed_files: int
    shared_settings: dict[str, Any]
    aggregate_original_size: int
    aggregate_compressed_size: int
    saved_bytes: int
    saved_percentage: float
    created_at: datetime
    updated_at: datetime
    finished_at: datetime | None
    jobs: list[JobResponse] = Field(default_factory=list)
