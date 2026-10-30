"""Image compression processor implementing BaseCompressionEngine."""

import io
from pathlib import Path
from typing import Any, BinaryIO, ClassVar

from PIL import Image

from app.engines.base import (
    BaseCompressionEngine,
    CompressionOptions,
    EngineResult,
    ImageFormat,
)
from app.engines.exceptions import (
    CorruptImageError,
    DecompressionBombError,
    OutputValidationError,
    UnsupportedFormatError,
)
from app.engines.image.formats import (
    detect_image_format,
    normalize_format,
)
from app.engines.image.metadata import (
    auto_orient_image,
    extract_metadata,
)
from app.engines.image.optimizer import ImageOptimizer
from app.engines.image.strategies import (
    handle_transparency,
)

# Protect against decompression bomb attacks (DoS) - max 100 megapixels
MAX_SAFE_PIXELS = 100_000_000
Image.MAX_IMAGE_PIXELS = MAX_SAFE_PIXELS


class ImageCompressionEngine(BaseCompressionEngine):
    """Production-grade image compression engine independent of FastAPI/Celery."""

    SUPPORTED_FORMATS: ClassVar[set[ImageFormat]] = {
        ImageFormat.JPEG,
        ImageFormat.PNG,
        ImageFormat.WEBP,
    }

    def can_handle(self, format_or_data: str | bytes) -> bool:
        """Check if format or raw data can be processed by this engine."""
        try:
            if isinstance(format_or_data, bytes):
                detected = detect_image_format(format_or_data)
                return detected in self.SUPPORTED_FORMATS
            normalized = normalize_format(format_or_data)
            return normalized in self.SUPPORTED_FORMATS
        except Exception:
            return False

    def inspect(self, input_data: bytes | BinaryIO | Path) -> dict[str, Any]:
        """Inspect image properties, dimensions, format, and metadata without full compression."""
        data = self._to_bytes(input_data)
        detected_format = detect_image_format(data)

        try:
            with Image.open(io.BytesIO(data)) as img:
                meta = extract_metadata(img)
                meta["file_size_bytes"] = len(data)
                meta["detected_format"] = detected_format.value
                return meta
        except Exception as exc:
            raise CorruptImageError(f"Failed to inspect image: {exc}") from exc

    def compress(
        self,
        input_data: bytes | BinaryIO | Path,
        options: CompressionOptions | None = None,
    ) -> EngineResult:
        """Execute full image compression pipeline with output validation."""
        opt = options or CompressionOptions()
        original_bytes = self._to_bytes(input_data)
        original_size = len(original_bytes)

        if original_size == 0:
            raise CorruptImageError("Input image data is empty")

        # 1. Format detection
        source_format = detect_image_format(original_bytes)
        target_format = opt.target_format or source_format

        if target_format not in self.SUPPORTED_FORMATS:
            raise UnsupportedFormatError(f"Unsupported target format: {target_format}")

        # 2. Decode image with Decompression Bomb guard
        try:
            pil_img = Image.open(io.BytesIO(original_bytes))
            # Verify basic structure
            pil_img.draft(pil_img.mode, pil_img.size)
        except Image.DecompressionBombError as exc:
            raise DecompressionBombError(
                f"Image exceeds safe pixel limit ({MAX_SAFE_PIXELS}): {exc}"
            ) from exc
        except Exception as exc:
            raise CorruptImageError(f"Could not open or decode image: {exc}") from exc

        try:
            # Check total pixels
            if pil_img.width * pil_img.height > MAX_SAFE_PIXELS:
                raise DecompressionBombError(
                    f"Image resolution {pil_img.width}x{pil_img.height} exceeds safe limit"
                )

            # 3. EXIF orientation correction
            oriented_img, was_reoriented = auto_orient_image(pil_img)
            original_width = oriented_img.width
            original_height = oriented_img.height

            # 4. Transparency and color mode handling
            prepared_img = handle_transparency(
                oriented_img,
                target_format=target_format,
                background_color=opt.background_color,
            )

            # 5. Compression: target-size optimization vs preset optimization
            if opt.target_size_bytes is not None:
                (
                    compressed_bytes,
                    final_width,
                    final_height,
                    target_achieved,
                    warning,
                    meta,
                ) = ImageOptimizer.optimize_for_target_size(
                    prepared_img,
                    format_type=target_format,
                    target_size_bytes=opt.target_size_bytes,
                    options=opt,
                )
            else:
                (
                    compressed_bytes,
                    final_width,
                    final_height,
                    meta,
                ) = ImageOptimizer.optimize_preset(
                    prepared_img,
                    format_type=target_format,
                    options=opt,
                )
                target_achieved = None
                warning = None

            # 6. Output validation
            self._validate_output(
                compressed_bytes,
                expected_format=target_format,
                expected_width=final_width,
                expected_height=final_height,
            )

            meta["was_reoriented"] = was_reoriented
            meta["source_format"] = source_format.value
            meta["target_format"] = target_format.value

            return EngineResult(
                data=compressed_bytes,
                original_size=original_size,
                compressed_size=len(compressed_bytes),
                format=target_format.value,
                width=final_width,
                height=final_height,
                original_width=original_width,
                original_height=original_height,
                target_achieved=target_achieved,
                warning=warning,
                metadata=meta,
            )

        finally:
            pil_img.close()

    def _validate_output(
        self,
        output_bytes: bytes,
        expected_format: ImageFormat,
        expected_width: int,
        expected_height: int,
    ) -> None:
        """Validate output image integrity, format, and dimensions."""
        if not output_bytes or len(output_bytes) < 12:
            raise OutputValidationError("Compressed image output is empty or truncated")

        try:
            with Image.open(io.BytesIO(output_bytes)) as verify_img:
                # Use PIL's built-in integrity check
                verify_img.verify()

            # Re-open after verify() (Pillow closes file pointer after verify)
            with Image.open(io.BytesIO(output_bytes)) as verify_img:
                out_format = detect_image_format(output_bytes)
                if out_format != expected_format:
                    raise OutputValidationError(
                        f"Expected format {expected_format.value}, got {out_format.value}"
                    )
                if verify_img.width != expected_width or verify_img.height != expected_height:
                    raise OutputValidationError(
                        f"Dimension mismatch: expected {expected_width}x{expected_height}, "
                        f"got {verify_img.width}x{verify_img.height}"
                    )
        except OutputValidationError:
            raise
        except Exception as exc:
            raise OutputValidationError(f"Generated image failed validation: {exc}") from exc

    def _to_bytes(self, input_data: bytes | BinaryIO | Path) -> bytes:
        """Convert input data source to bytes."""
        if isinstance(input_data, bytes):
            return input_data
        if isinstance(input_data, Path):
            return input_data.read_bytes()
        if hasattr(input_data, "read"):
            pos = input_data.tell() if hasattr(input_data, "tell") else 0
            content = input_data.read()
            if hasattr(input_data, "seek"):
                input_data.seek(pos)
            return content
        raise ValueError(f"Unsupported input data type: {type(input_data)}")
