"""Image format detection, MIME mappings, and capabilities."""

import io
from enum import StrEnum
from typing import Final

from PIL import Image

from app.engines.base import ImageFormat
from app.engines.exceptions import UnsupportedFormatError


class FormatCapability(StrEnum):
    """Capabilities supported by image formats."""

    TRANSPARENCY = "transparency"
    ANIMATION = "animation"
    LOSSY = "lossy"
    LOSSLESS = "lossless"
    EXIF = "exif"
    ICC = "icc"


MAGIC_SIGNATURES: Final[list[tuple[bytes, ImageFormat]]] = [
    (b"\xff\xd8\xff", ImageFormat.JPEG),
    (b"\x89PNG\r\n\x1a\n", ImageFormat.PNG),
]

MIME_TO_FORMAT: Final[dict[str, ImageFormat]] = {
    "image/jpeg": ImageFormat.JPEG,
    "image/jpg": ImageFormat.JPEG,
    "image/pjpeg": ImageFormat.JPEG,
    "image/png": ImageFormat.PNG,
    "image/x-png": ImageFormat.PNG,
    "image/webp": ImageFormat.WEBP,
}

EXTENSION_TO_FORMAT: Final[dict[str, ImageFormat]] = {
    ".jpg": ImageFormat.JPEG,
    ".jpeg": ImageFormat.JPEG,
    ".png": ImageFormat.PNG,
    ".webp": ImageFormat.WEBP,
}

FORMAT_TO_MIME: Final[dict[ImageFormat, str]] = {
    ImageFormat.JPEG: "image/jpeg",
    ImageFormat.PNG: "image/png",
    ImageFormat.WEBP: "image/webp",
}

FORMAT_CAPABILITIES: Final[dict[ImageFormat, set[FormatCapability]]] = {
    ImageFormat.JPEG: {
        FormatCapability.LOSSY,
        FormatCapability.EXIF,
        FormatCapability.ICC,
    },
    ImageFormat.PNG: {
        FormatCapability.TRANSPARENCY,
        FormatCapability.LOSSLESS,
        FormatCapability.ICC,
        FormatCapability.EXIF,
    },
    ImageFormat.WEBP: {
        FormatCapability.TRANSPARENCY,
        FormatCapability.LOSSY,
        FormatCapability.LOSSLESS,
        FormatCapability.ANIMATION,
        FormatCapability.ICC,
        FormatCapability.EXIF,
    },
}


def detect_image_format(data: bytes) -> ImageFormat:
    """Detect image format reliably using magic bytes, then Pillow inspection."""
    if len(data) < 12:
        raise UnsupportedFormatError("Input data too small to identify format")

    # Fast magic bytes detection
    for signature, img_format in MAGIC_SIGNATURES:
        if data.startswith(signature):
            return img_format

    # WebP check: starts with RIFF, then 4 bytes of size, then WEBP
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return ImageFormat.WEBP

    # Fallback to Pillow format detection
    try:
        with Image.open(io.BytesIO(data)) as img:
            pil_format = (img.format or "").upper()
            if pil_format in ("JPEG", "JPG"):
                return ImageFormat.JPEG
            if pil_format == "PNG":
                return ImageFormat.PNG
            if pil_format == "WEBP":
                return ImageFormat.WEBP
    except Exception as exc:
        raise UnsupportedFormatError(f"Could not determine image format: {exc}") from exc

    raise UnsupportedFormatError(f"Unsupported image format: {data[:16]!r}")


def normalize_format(format_hint: str | ImageFormat) -> ImageFormat:
    """Convert string MIME, extension, or name to ImageFormat."""
    if isinstance(format_hint, ImageFormat):
        return format_hint

    cleaned = format_hint.strip().lower()
    if cleaned in MIME_TO_FORMAT:
        return MIME_TO_FORMAT[cleaned]

    cleaned_ext = f".{cleaned.lstrip('.')}"
    if cleaned_ext in EXTENSION_TO_FORMAT:
        return EXTENSION_TO_FORMAT[cleaned_ext]

    if cleaned in ("jpeg", "jpg"):
        return ImageFormat.JPEG
    if cleaned == "png":
        return ImageFormat.PNG
    if cleaned == "webp":
        return ImageFormat.WEBP

    raise UnsupportedFormatError(f"Unknown format specification: {format_hint}")
