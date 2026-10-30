"""Tests for PDF target-size optimization and edge cases."""

import pytest
from app.engines.base import CompressionOptions
from app.engines.exceptions import TargetSizeUnachievableError
from app.engines.pdf.processor import PDFCompressionEngine


def test_pdf_target_size_achievable(sample_text_pdf_bytes: bytes) -> None:
    engine = PDFCompressionEngine()
    # Generous target size of 200 KB
    target_bytes = 200 * 1024

    opts = CompressionOptions(target_size_bytes=target_bytes)
    res = engine.compress(sample_text_pdf_bytes, opts)

    assert res.target_achieved is True
    assert res.compressed_size <= target_bytes


def test_pdf_target_size_unachievable_non_strict(sample_image_pdf_bytes: bytes) -> None:
    engine = PDFCompressionEngine()
    # Tiny impossible target size of 100 bytes
    tiny_target = 100

    opts = CompressionOptions(
        target_size_bytes=tiny_target,
        strict_target_size=False,
    )
    res = engine.compress(sample_image_pdf_bytes, opts)

    assert res.target_achieved is False
    assert res.warning is not None
    assert "could not be reached safely" in res.warning
    assert res.compressed_size > 0


def test_pdf_target_size_unachievable_strict(sample_image_pdf_bytes: bytes) -> None:
    engine = PDFCompressionEngine()
    tiny_target = 100

    opts = CompressionOptions(
        target_size_bytes=tiny_target,
        strict_target_size=True,
    )

    with pytest.raises(TargetSizeUnachievableError):
        engine.compress(sample_image_pdf_bytes, opts)
