"""Coordination service combining storage, database jobs, and compression engines."""

import uuid
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.database.models import CompressionJob
from app.engines.base import CompressionOptions, CompressionPreset
from app.engines.exceptions import (
    CompressionError,
    CorruptImageError,
    CorruptPDFError,
    EncryptedPDFError,
    TargetSizeUnachievableError,
    UnsupportedFormatError,
)
from app.engines.image.formats import detect_image_format, normalize_format
from app.engines.optimizer import parse_target_size
from app.engines.registry import get_engine_registry
from app.schemas.job import JobCreate
from app.services.batch_service import BatchService
from app.services.job_service import JobService
from app.services.storage_service import StorageService, get_storage_service


class CompressionService:
    """Coordinates file ingestion, engine compression, storage, and persistence."""

    def __init__(self, storage: StorageService | None = None) -> None:
        self.storage = storage or get_storage_service()
        self.registry = get_engine_registry()
        self.settings = get_settings()

    async def process_single_file(
        self,
        session: AsyncSession,
        content: bytes,
        filename: str,
        preset: str | CompressionPreset = CompressionPreset.BALANCED,
        target_size: str | int | None = None,
        quality: int | None = None,
        max_dimension: int | None = None,
        target_format: str | None = None,
        batch_id: uuid.UUID | None = None,
    ) -> CompressionJob:
        """Execute full end-to-end compression pipeline for a single file."""
        if len(content) == 0:
            raise CorruptImageError("Uploaded file is empty (0 bytes)")

        max_allowed_bytes = self.settings.MAX_FILE_SIZE_MB * 1024 * 1024
        if len(content) > max_allowed_bytes:
            raise ValueError(
                f"File size exceeds maximum allowed limit of {self.settings.MAX_FILE_SIZE_MB} MB"
            )

        # 1. Determine engine and format
        engine = self.registry.get_engine_for_data(content)

        ext = Path(filename).suffix.lower().lstrip(".")
        if content.startswith(b"%PDF-") or ext == "pdf":
            detected_format = "pdf"
        else:
            try:
                detected_format = detect_image_format(content).value
            except Exception:
                try:
                    detected_format = normalize_format(ext).value
                except Exception:
                    detected_format = ext or "unknown"

        # 2. Store raw uploaded file
        raw_ref, _ = self.storage.save_file(content, filename=filename, is_output=False)

        # 3. Build options
        parsed_preset = CompressionPreset(preset) if isinstance(preset, str) else preset
        parsed_target_size = parse_target_size(target_size) if target_size is not None else None

        opts = CompressionOptions(
            preset=parsed_preset,
            target_size_bytes=parsed_target_size,
            quality=quality,
            max_dimension=max_dimension,
            strict_target_size=False,
        )

        # 4. Create initial database job record in PENDING state
        job_create = JobCreate(
            batch_id=batch_id,
            original_file_reference=raw_ref,
            original_filename=filename,
            original_size=len(content),
            file_format=detected_format,
            compression_preset=parsed_preset.value if parsed_preset else None,
            target_size=parsed_target_size,
        )
        job = await JobService.create_job(session, job_create)

        # 5. Execute compression
        try:
            result = engine.compress(content, options=opts)

            # Store compressed output
            output_ref, _ = self.storage.save_file(
                result.data,
                filename=f"compressed_{filename}",
                is_output=True,
            )

            # Update job record to COMPLETED
            job = await JobService.mark_completed(
                session,
                job_id=job.id,
                output_file_reference=output_ref,
                output_size=result.compressed_size,
                target_achieved=result.target_achieved,
                warning_message=result.warning,
                metadata_update=result.metadata,
            )
            assert job is not None

        except (
            CorruptImageError,
            CorruptPDFError,
            EncryptedPDFError,
            UnsupportedFormatError,
            TargetSizeUnachievableError,
            CompressionError,
            Exception,
        ) as exc:
            error_msg = str(exc)
            job = await JobService.mark_failed(session, job.id, error_message=error_msg)
            assert job is not None

        # 6. Recalculate parent batch if associated
        if batch_id is not None:
            await BatchService.recalculate_batch(session, batch_id)

        return job
