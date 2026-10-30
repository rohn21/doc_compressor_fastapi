"""Tests for PDF compression strategies (Lossless, Image Optimization, Aggressive)."""

import pymupdf
from app.engines.pdf.strategies import (
    apply_aggressive_strategy,
    apply_image_optimization_strategy,
    apply_lossless_strategy,
)
from app.engines.pdf.validator import validate_pdf_output


def test_apply_lossless_strategy(sample_text_pdf_bytes: bytes) -> None:
    doc = pymupdf.open(stream=sample_text_pdf_bytes, filetype="pdf")
    try:
        compressed_bytes = apply_lossless_strategy(doc)
        assert len(compressed_bytes) > 0
        assert compressed_bytes.startswith(b"%PDF-")

        # Validate that structure and text are intact
        info = validate_pdf_output(compressed_bytes, expected_page_count=3)
        assert info["page_count"] == 3
    finally:
        doc.close()


def test_apply_image_optimization_strategy(sample_image_pdf_bytes: bytes) -> None:
    doc = pymupdf.open(stream=sample_image_pdf_bytes, filetype="pdf")
    try:
        compressed_bytes = apply_image_optimization_strategy(
            doc,
            dpi_threshold=200,
            dpi_target=150,
            quality=80,
        )
        assert len(compressed_bytes) > 0
        assert compressed_bytes.startswith(b"%PDF-")

        info = validate_pdf_output(compressed_bytes, expected_page_count=1)
        assert info["page_count"] == 1
    finally:
        doc.close()


def test_apply_aggressive_strategy_with_grayscale(sample_image_pdf_bytes: bytes) -> None:
    doc = pymupdf.open(stream=sample_image_pdf_bytes, filetype="pdf")
    try:
        compressed_bytes, warnings = apply_aggressive_strategy(
            doc,
            dpi_threshold=96,
            dpi_target=72,
            quality=50,
            set_to_gray=True,
        )
        assert len(compressed_bytes) > 0
        assert len(warnings) >= 2
        assert any("grayscale" in w for w in warnings)

        info = validate_pdf_output(compressed_bytes, expected_page_count=1)
        assert info["page_count"] == 1
    finally:
        doc.close()
