"""Validation and structural verification for generated PDF documents."""

from typing import Any

import pymupdf

from app.engines.exceptions import OutputValidationError


def validate_pdf_output(
    pdf_bytes: bytes,
    expected_page_count: int | None = None,
) -> dict[str, Any]:
    """Verify that compressed PDF output opens successfully, retains pages, and is readable.

    Raises OutputValidationError if output fails integrity or readability checks.
    """
    if not pdf_bytes or len(pdf_bytes) < 32:
        raise OutputValidationError("Compressed PDF is empty or truncated")

    if not pdf_bytes.startswith(b"%PDF-"):
        raise OutputValidationError("Compressed output lacks valid PDF file signature")

    try:
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:
        raise OutputValidationError(f"Generated PDF cannot be opened: {exc}") from exc

    try:
        if doc.is_encrypted:
            raise OutputValidationError("Generated PDF was unexpectedly left encrypted")

        page_count = len(doc)
        if page_count == 0:
            raise OutputValidationError("Generated PDF contains 0 pages")

        if expected_page_count is not None and page_count != expected_page_count:
            raise OutputValidationError(
                f"Page count mismatch: expected {expected_page_count}, got {page_count}"
            )

        # Validate that each page is loadable and renders correctly
        for page_idx in range(page_count):
            page = doc.load_page(page_idx)
            if page.rect.is_empty or page.rect.is_infinite:
                msg = f"Page {page_idx + 1} has invalid dimensions: {page.rect}"
                raise OutputValidationError(msg)
            # Ensure text / draw commands can be parsed
            _ = page.get_drawings()

        first_page = doc.load_page(0)
        return {
            "page_count": page_count,
            "first_page_width": round(first_page.rect.width),
            "first_page_height": round(first_page.rect.height),
            "has_signatures": doc.get_sigflags() > 0,
            "is_form_pdf": bool(doc.is_form_pdf),
        }

    except OutputValidationError:
        raise
    except Exception as exc:
        raise OutputValidationError(f"Failed to read and validate PDF pages: {exc}") from exc
    finally:
        doc.close()
