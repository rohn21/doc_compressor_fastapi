"""Tests for engine registry routing and format discovery."""

import pytest
from app.engines.base import ImageFormat
from app.engines.exceptions import UnsupportedFormatError
from app.engines.image.processor import ImageCompressionEngine
from app.engines.optimizer import build_compression_options, parse_target_size
from app.engines.registry import get_engine_registry


def test_registry_lookup_by_format() -> None:
    registry = get_engine_registry()
    engine = registry.get_engine_for_format("jpeg")
    assert isinstance(engine, ImageCompressionEngine)

    engine_png = registry.get_engine_for_format(ImageFormat.PNG)
    assert isinstance(engine_png, ImageCompressionEngine)


def test_registry_lookup_by_data(
    sample_rgb_bytes: bytes,
    sample_text_pdf_bytes: bytes,
) -> None:
    from app.engines.pdf.processor import PDFCompressionEngine

    registry = get_engine_registry()
    engine_img = registry.get_engine_for_data(sample_rgb_bytes)
    assert isinstance(engine_img, ImageCompressionEngine)

    engine_pdf = registry.get_engine_for_data(sample_text_pdf_bytes)
    assert isinstance(engine_pdf, PDFCompressionEngine)

    engine_pdf_fmt = registry.get_engine_for_format("pdf")
    assert isinstance(engine_pdf_fmt, PDFCompressionEngine)


def test_registry_unsupported_format() -> None:
    registry = get_engine_registry()
    with pytest.raises(UnsupportedFormatError):
        registry.get_engine_for_format("unknown_xyz")


def test_parse_target_size() -> None:
    assert parse_target_size("50KB") == 50 * 1024
    assert parse_target_size("200KB") == 200 * 1024
    assert parse_target_size("1MB") == 1024 * 1024
    assert parse_target_size(50000) == 50000


def test_build_compression_options() -> None:
    opts = build_compression_options(preset="high_quality", target_size="100KB")
    assert opts.preset.value == "high_quality"
    assert opts.target_size_bytes == 100 * 1024
