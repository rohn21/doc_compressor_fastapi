"""Tests for PDFCompressionEngine, presets, edge cases, forms, and signatures."""

import pytest
from app.engines.base import CompressionOptions, CompressionPreset
from app.engines.exceptions import (
    CorruptPDFError,
    EncryptedPDFError,
    UnsupportedFormatError,
)
from app.engines.pdf.processor import PDFCompressionEngine


def test_pdf_can_handle() -> None:
    engine = PDFCompressionEngine()
    assert engine.can_handle("pdf") is True
    assert engine.can_handle("application/pdf") is True
    assert engine.can_handle(".pdf") is True
    assert engine.can_handle(b"%PDF-1.7\n...") is True
    assert engine.can_handle("image/jpeg") is False
    assert engine.can_handle(b"\xff\xd8\xff") is False


def test_pdf_inspect(sample_text_pdf_bytes: bytes, sample_form_pdf_bytes: bytes) -> None:
    engine = PDFCompressionEngine()
    meta = engine.inspect(sample_text_pdf_bytes)

    assert meta["format"] == "pdf"
    assert meta["page_count"] == 3
    assert meta["is_encrypted"] is False
    assert meta["first_page_width"] == 595
    assert meta["first_page_height"] == 842

    form_meta = engine.inspect(sample_form_pdf_bytes)
    assert form_meta["is_form_pdf"] is True


def test_pdf_compress_presets(sample_image_pdf_bytes: bytes) -> None:
    engine = PDFCompressionEngine()

    # High Quality (Lossless)
    res_hq = engine.compress(
        sample_image_pdf_bytes,
        CompressionOptions(preset=CompressionPreset.HIGH_QUALITY),
    )
    assert res_hq.original_size > 0
    assert res_hq.compressed_size > 0

    # Balanced preset
    res_bal = engine.compress(
        sample_image_pdf_bytes,
        CompressionOptions(preset=CompressionPreset.BALANCED),
    )
    assert res_bal.compressed_size > 0

    # Maximum preset
    res_max = engine.compress(
        sample_image_pdf_bytes,
        CompressionOptions(preset=CompressionPreset.MAXIMUM),
    )
    assert res_max.compressed_size > 0
    assert res_max.warning is not None


def test_pdf_encrypted_edge_case(sample_encrypted_pdf_bytes: bytes) -> None:
    engine = PDFCompressionEngine()
    with pytest.raises(EncryptedPDFError):
        engine.compress(sample_encrypted_pdf_bytes)


def test_pdf_digital_signatures_warning(sample_signed_pdf_bytes: bytes) -> None:
    engine = PDFCompressionEngine()
    res = engine.compress(sample_signed_pdf_bytes)
    assert res.warning is not None
    assert "Digital signatures detected" in res.warning


def test_pdf_form_preservation(sample_form_pdf_bytes: bytes) -> None:
    engine = PDFCompressionEngine()
    res = engine.compress(sample_form_pdf_bytes)
    assert res.metadata.get("is_form_pdf") is True


def test_pdf_corrupt_or_empty() -> None:
    engine = PDFCompressionEngine()
    with pytest.raises(CorruptPDFError):
        engine.compress(b"")

    with pytest.raises(UnsupportedFormatError):
        engine.compress(b"random-bytes-not-a-pdf")
