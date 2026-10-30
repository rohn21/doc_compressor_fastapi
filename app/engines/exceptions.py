"""Exceptions for compression engines.

These exceptions are strictly domain-level and independent of HTTP/FastAPI,
allowing the compression engine to be used in any Python application.
"""


class CompressionError(Exception):
    """Base exception for all compression engine errors."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class UnsupportedFormatError(CompressionError):
    """Raised when the input file format is not supported."""


class CorruptImageError(CompressionError):
    """Raised when the image data cannot be decoded or is corrupt."""


class DecompressionBombError(CompressionError):
    """Raised when an image exceeds safe dimensions or pixel count."""


class TargetSizeUnachievableError(CompressionError):
    """Raised when target file size cannot be achieved within safe quality/dimension bounds."""


class OutputValidationError(CompressionError):
    """Raised when the compressed output fails integrity or format validation."""
