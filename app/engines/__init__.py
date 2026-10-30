"""Document and image compression engines package."""

from app.engines.base import (
    PRESET_CONFIGS,
    BaseCompressionEngine,
    CompressionOptions,
    CompressionPreset,
    EngineResult,
    ImageFormat,
    PresetConfig,
)
from app.engines.exceptions import (
    CompressionError,
    CorruptImageError,
    CorruptPDFError,
    DecompressionBombError,
    EncryptedPDFError,
    OutputValidationError,
    TargetSizeUnachievableError,
    UnsupportedFormatError,
)
from app.engines.optimizer import build_compression_options, parse_target_size
from app.engines.registry import EngineRegistry, get_engine_registry

__all__ = [
    "PRESET_CONFIGS",
    "BaseCompressionEngine",
    "CompressionError",
    "CompressionOptions",
    "CompressionPreset",
    "CorruptImageError",
    "CorruptPDFError",
    "DecompressionBombError",
    "EncryptedPDFError",
    "EngineRegistry",
    "EngineResult",
    "ImageFormat",
    "OutputValidationError",
    "PresetConfig",
    "TargetSizeUnachievableError",
    "UnsupportedFormatError",
    "build_compression_options",
    "get_engine_registry",
    "parse_target_size",
]
