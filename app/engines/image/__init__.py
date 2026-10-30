"""Image compression engine package."""

from app.engines.image.analyzer import ImageAnalyzer
from app.engines.image.formats import detect_image_format, normalize_format
from app.engines.image.metadata import auto_orient_image, extract_metadata
from app.engines.image.optimizer import ImageOptimizer
from app.engines.image.processor import ImageCompressionEngine

__all__ = [
    "ImageAnalyzer",
    "ImageCompressionEngine",
    "ImageOptimizer",
    "auto_orient_image",
    "detect_image_format",
    "extract_metadata",
    "normalize_format",
]
