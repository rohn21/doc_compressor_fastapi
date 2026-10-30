"""Base models, configurations, and interfaces for compression engines."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, BinaryIO


class CompressionPreset(StrEnum):
    """Standard compression presets offering initial policy benchmarks."""

    HIGH_QUALITY = "high_quality"
    BALANCED = "balanced"
    MEDIUM = "medium"
    MAXIMUM = "maximum"


class ImageFormat(StrEnum):
    """Supported image file formats."""

    JPEG = "jpeg"
    PNG = "png"
    WEBP = "webp"
    PDF = "pdf"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class PresetConfig:
    """Preset configuration parameters."""

    max_dimension: int
    starting_quality: int
    webp_quality: int
    png_compress_level: int
    png_optimize: bool = True


PRESET_CONFIGS: dict[CompressionPreset, PresetConfig] = {
    CompressionPreset.HIGH_QUALITY: PresetConfig(
        max_dimension=2560,
        starting_quality=92,
        webp_quality=88,
        png_compress_level=7,
        png_optimize=True,
    ),
    CompressionPreset.BALANCED: PresetConfig(
        max_dimension=1920,
        starting_quality=82,
        webp_quality=80,
        png_compress_level=8,
        png_optimize=True,
    ),
    CompressionPreset.MEDIUM: PresetConfig(
        max_dimension=1600,
        starting_quality=68,
        webp_quality=65,
        png_compress_level=9,
        png_optimize=True,
    ),
    CompressionPreset.MAXIMUM: PresetConfig(
        max_dimension=1200,
        starting_quality=48,
        webp_quality=45,
        png_compress_level=9,
        png_optimize=True,
    ),
}


@dataclass
class CompressionOptions:
    """Configurable options for image and document compression."""

    preset: CompressionPreset = CompressionPreset.BALANCED
    target_size_bytes: int | None = None
    quality: int | None = None
    max_dimension: int | None = None
    target_format: ImageFormat | None = None
    preserve_metadata: bool = False
    preserve_icc: bool = True
    strip_exif: bool = True
    background_color: tuple[int, int, int] = (255, 255, 255)
    allow_upscaling: bool = False
    strict_target_size: bool = False


@dataclass
class EngineResult:
    """Standard result returned by any compression engine."""

    data: bytes
    original_size: int
    compressed_size: int
    format: str
    width: int
    height: int
    original_width: int
    original_height: int
    saved_bytes: int = field(init=False)
    saved_percentage: float = field(init=False)
    target_achieved: bool | None = None
    warning: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.saved_bytes = max(0, self.original_size - self.compressed_size)
        if self.original_size > 0:
            pct = ((self.original_size - self.compressed_size) / self.original_size) * 100.0
            self.saved_percentage = round(pct, 2)
        else:
            self.saved_percentage = 0.0


class BaseCompressionEngine(ABC):
    """Abstract base class for all file compression engines."""

    @abstractmethod
    def can_handle(self, format_or_data: str | bytes) -> bool:
        """Check if this engine can process the given format or raw data."""

    @abstractmethod
    def inspect(self, input_data: bytes | BinaryIO | Path) -> dict[str, Any]:
        """Inspect file metadata, dimensions, and properties without full compression."""

    @abstractmethod
    def compress(
        self,
        input_data: bytes | BinaryIO | Path,
        options: CompressionOptions | None = None,
    ) -> EngineResult:
        """Compress input data using specified options."""
