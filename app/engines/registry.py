"""Central engine registry for routing compression tasks to appropriate engines."""

from app.engines.base import BaseCompressionEngine, ImageFormat
from app.engines.exceptions import UnsupportedFormatError
from app.engines.image.formats import detect_image_format, normalize_format
from app.engines.image.processor import ImageCompressionEngine
from app.engines.pdf.processor import PDFCompressionEngine


class EngineRegistry:
    """Registry coordinating available compression engines."""

    def __init__(self) -> None:
        self._engines: list[BaseCompressionEngine] = []
        self._register_default_engines()

    def _register_default_engines(self) -> None:
        """Register default engines."""
        self.register(ImageCompressionEngine())
        self.register(PDFCompressionEngine())

    def register(self, engine: BaseCompressionEngine) -> None:
        """Register a compression engine."""
        self._engines.append(engine)

    def get_engine_for_format(self, format_spec: str | ImageFormat) -> BaseCompressionEngine:
        """Find an engine capable of handling the specified format."""
        try:
            norm = normalize_format(format_spec)
            for engine in self._engines:
                if engine.can_handle(norm.value):
                    return engine
        except Exception:
            # If not normalized as image, check raw string (e.g. 'pdf')
            for engine in self._engines:
                if engine.can_handle(str(format_spec)):
                    return engine

        raise UnsupportedFormatError(f"No compression engine registered for format: {format_spec}")

    def get_engine_for_data(self, data: bytes) -> BaseCompressionEngine:
        """Find an engine capable of handling raw binary data."""
        if len(data) < 4:
            raise UnsupportedFormatError("Input data too short to identify format")

        # Check PDF header before image magic bytes
        if data.startswith(b"%PDF"):
            for engine in self._engines:
                if engine.can_handle("pdf") or engine.can_handle(data):
                    return engine

        # Try image detection
        try:
            fmt = detect_image_format(data)
            for engine in self._engines:
                if engine.can_handle(fmt.value) or engine.can_handle(data):
                    return engine
        except UnsupportedFormatError:
            pass

        # Fallback to checking each registered engine
        for engine in self._engines:
            if engine.can_handle(data):
                return engine

        raise UnsupportedFormatError("No compression engine registered for provided file data")


# Global registry singleton
_registry: EngineRegistry | None = None


def get_engine_registry() -> EngineRegistry:
    """Retrieve global engine registry instance."""
    global _registry
    if _registry is None:
        _registry = EngineRegistry()
    return _registry
