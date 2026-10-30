"""Pydantic schemas for compression jobs."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.database.models.enums import JobStatus


class JobBase(BaseModel):
    """Base job attributes."""

    original_filename: str
    file_format: str
    compression_preset: str | None = None
    target_size: int | None = None


class JobCreate(JobBase):
    """Schema for creating a compression job."""

    batch_id: uuid.UUID | None = None
    original_file_reference: str
    original_size: int = Field(gt=0)
    job_metadata: dict[str, Any] = Field(default_factory=dict)


class JobUpdate(BaseModel):
    """Schema for updating job status and results."""

    status: JobStatus | None = None
    output_file_reference: str | None = None
    output_size: int | None = None
    target_achieved: bool | None = None
    warning_message: str | None = None
    error_message: str | None = None
    finished_at: datetime | None = None
    job_metadata: dict[str, Any] | None = None


class JobResponse(JobBase):
    """Schema for returning job state and metrics."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    batch_id: uuid.UUID | None
    original_file_reference: str
    output_file_reference: str | None
    original_size: int
    output_size: int | None
    status: JobStatus
    target_achieved: bool | None
    warning_message: str | None
    error_message: str | None
    saved_bytes: int
    saved_percentage: float
    created_at: datetime
    updated_at: datetime
    finished_at: datetime | None
    job_metadata: dict[str, Any]
