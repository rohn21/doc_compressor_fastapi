"""High-level compression optimizer coordination and helpers."""

from typing import Final

from app.engines.base import CompressionOptions, CompressionPreset, ImageFormat

STANDARD_TARGET_SIZES_KB: Final[dict[str, int]] = {
    "50KB": 50 * 1024,
    "100KB": 100 * 1024,
    "200KB": 200 * 1024,
    "500KB": 500 * 1024,
}


def parse_target_size(size_val: str | int) -> int:
    """Parse standard target size strings (e.g. '50KB', '200KB', '1MB') or bytes int into bytes."""
    if isinstance(size_val, int):
        if size_val <= 0:
            raise ValueError(f"Target size must be positive: {size_val}")
        return size_val

    cleaned = size_val.strip().upper()
    if cleaned in STANDARD_TARGET_SIZES_KB:
        return STANDARD_TARGET_SIZES_KB[cleaned]

    if cleaned.endswith("KB"):
        return int(float(cleaned[:-2].strip()) * 1024)
    if cleaned.endswith("MB"):
        return int(float(cleaned[:-2].strip()) * 1024 * 1024)
    if cleaned.endswith("B"):
        return int(cleaned[:-1].strip())

    return int(cleaned)


def build_compression_options(
    preset: str | CompressionPreset = CompressionPreset.BALANCED,
    target_size: str | int | None = None,
    quality: int | None = None,
    max_dimension: int | None = None,
    target_format: str | ImageFormat | None = None,
    preserve_metadata: bool = False,
    preserve_icc: bool = True,
    strict_target_size: bool = False,
) -> CompressionOptions:
    """Helper to build validated CompressionOptions."""
    parsed_preset = CompressionPreset(preset) if isinstance(preset, str) else preset
    parsed_target_size = parse_target_size(target_size) if target_size is not None else None
    parsed_format = (
        ImageFormat(target_format.lower()) if isinstance(target_format, str) else target_format
    )

    return CompressionOptions(
        preset=parsed_preset,
        target_size_bytes=parsed_target_size,
        quality=quality,
        max_dimension=max_dimension,
        target_format=parsed_format,
        preserve_metadata=preserve_metadata,
        preserve_icc=preserve_icc,
        strict_target_size=strict_target_size,
    )
