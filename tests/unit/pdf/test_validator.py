"""Tests for PDF output validator and structural integrity checks."""

import pytest
from app.engines.exceptions import OutputValidationError
from app.engines.pdf.validator import validate_pdf_output


def test_validate_pdf_output_valid(sample_text_pdf_bytes: bytes) -> None:
    info = validate_pdf_output(sample_text_pdf_bytes, expected_page_count=3)
    assert info["page_count"] == 3
    assert info["first_page_width"] == 595
    assert info["first_page_height"] == 842


def test_validate_pdf_output_empty() -> None:
    with pytest.raises(OutputValidationError, match="empty or truncated"):
        validate_pdf_output(b"")


def test_validate_pdf_output_invalid_signature() -> None:
    with pytest.raises(OutputValidationError, match="lacks valid PDF file signature"):
        validate_pdf_output(b"not-a-pdf-content-here-at-all-1234567890")


def test_validate_pdf_output_page_count_mismatch(sample_text_pdf_bytes: bytes) -> None:
    with pytest.raises(OutputValidationError, match="Page count mismatch"):
        validate_pdf_output(sample_text_pdf_bytes, expected_page_count=10)
