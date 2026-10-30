"""Compression strategies for PDF documents using PyMuPDF."""

from enum import StrEnum

import pymupdf


class PDFStrategy(StrEnum):
    """PDF compression strategy tiers."""

    LOSSLESS = "lossless"
    IMAGE_OPTIMIZATION = "image_optimization"
    AGGRESSIVE = "aggressive"


def apply_lossless_strategy(doc: pymupdf.Document) -> bytes:
    """Execute lossless PDF optimization.

    - Removes unreferenced objects and compacts xref table (garbage=4).
    - Deflates content streams, embedded fonts, and embedded images (deflate=True).
    - Sanitizes document structure (clean=True).
    - Preserves all vector graphics, fonts, text, interactive forms, and annotations.
    """
    return doc.tobytes(
        garbage=4,
        clean=True,
        deflate=True,
        deflate_images=True,
        deflate_fonts=True,
    )


def apply_image_optimization_strategy(
    doc: pymupdf.Document,
    dpi_threshold: int = 200,
    dpi_target: int = 150,
    quality: int = 80,
) -> bytes:
    """Execute image downsampling and optimization on embedded images.

    - Inspects embedded images and downsamples those exceeding dpi_threshold to dpi_target.
    - Recompresses lossy images using target JPEG quality.
    - Preserves all text, vector content, forms, and annotations intact.
    """
    doc.rewrite_images(
        dpi_threshold=dpi_threshold,
        dpi_target=dpi_target,
        quality=quality,
        lossy=True,
        lossless=False,
        bitonal=False,
        color=True,
        gray=True,
        set_to_gray=False,
    )

    return doc.tobytes(
        garbage=4,
        clean=True,
        deflate=True,
        deflate_images=True,
        deflate_fonts=True,
    )


def apply_aggressive_strategy(
    doc: pymupdf.Document,
    dpi_threshold: int = 100,
    dpi_target: int = 72,
    quality: int = 50,
    set_to_gray: bool = False,
) -> tuple[bytes, list[str]]:
    """Execute aggressive compression with lower image resolution and optional grayscale.

    Returns the compressed PDF bytes and a list of warnings about potential quality loss.
    """
    warnings: list[str] = [
        f"Aggressive compression applied: embedded images downsampled to {dpi_target} DPI "
        f"at quality {quality}."
    ]

    if set_to_gray:
        warnings.append("Document colors were converted to grayscale.")

    doc.rewrite_images(
        dpi_threshold=dpi_threshold,
        dpi_target=dpi_target,
        quality=quality,
        lossy=True,
        lossless=True,
        bitonal=True,
        color=True,
        gray=True,
        set_to_gray=set_to_gray,
    )

    data = doc.tobytes(
        garbage=4,
        clean=True,
        deflate=True,
        deflate_images=True,
        deflate_fonts=True,
    )

    return data, warnings
