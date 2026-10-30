"""PDF compression processor implementing BaseCompressionEngine with PyMuPDF."""

from pathlib import Path
from typing import Any, BinaryIO

import pymupdf

from app.engines.base import (
    BaseCompressionEngine,
    CompressionOptions,
    EngineResult,
    ImageFormat,
)
from app.engines.exceptions import (
    CorruptPDFError,
    EncryptedPDFError,
    UnsupportedFormatError,
)
from app.engines.pdf.optimizer import PDFOptimizer
from app.engines.pdf.validator import validate_pdf_output


class PDFCompressionEngine(BaseCompressionEngine):
    """Production-grade PDF compression engine independent of FastAPI/Celery."""

    def can_handle(self, format_or_data: str | bytes) -> bool:
        """Check if format or raw data is a PDF."""
        if isinstance(format_or_data, bytes):
            return format_or_data.startswith(b"%PDF")
        cleaned = str(format_or_data).lower().strip().lstrip(".")
        return cleaned in ("pdf", "application/pdf")

    def inspect(self, input_data: bytes | BinaryIO | Path) -> dict[str, Any]:
        """Inspect PDF properties, page count, encryption, forms, and signatures."""
        data = self._to_bytes(input_data)
        if not data.startswith(b"%PDF"):
            raise UnsupportedFormatError("Input data is not a valid PDF file")

        try:
            doc = pymupdf.open(stream=data, filetype="pdf")
        except Exception as exc:
            raise CorruptPDFError(f"Failed to open PDF for inspection: {exc}") from exc

        try:
            is_enc = doc.is_encrypted
            has_signatures = doc.get_sigflags() > 0
            page_count = len(doc)
            is_form = bool(doc.is_form_pdf)
            has_annots = doc.has_annots()

            total_images = 0
            if not is_enc:
                for page in doc:
                    total_images += len(page.get_images())

            first_page_width = 0
            first_page_height = 0
            if page_count > 0 and not is_enc:
                rect = doc[0].rect
                first_page_width = round(rect.width)
                first_page_height = round(rect.height)

            return {
                "file_size_bytes": len(data),
                "format": "pdf",
                "page_count": page_count,
                "first_page_width": first_page_width,
                "first_page_height": first_page_height,
                "is_encrypted": is_enc,
                "has_signatures": has_signatures,
                "is_form_pdf": is_form,
                "has_annotations": has_annots,
                "embedded_images_count": total_images,
            }
        finally:
            doc.close()

    def compress(
        self,
        input_data: bytes | BinaryIO | Path,
        options: CompressionOptions | None = None,
    ) -> EngineResult:
        """Compress PDF document using specified options."""
        opt = options or CompressionOptions()
        original_bytes = self._to_bytes(input_data)
        original_size = len(original_bytes)

        if original_size == 0:
            raise CorruptPDFError("Input PDF data is empty")

        if not original_bytes.startswith(b"%PDF"):
            raise UnsupportedFormatError("Input data lacks PDF file signature")

        try:
            doc = pymupdf.open(stream=original_bytes, filetype="pdf")
        except Exception as exc:
            raise CorruptPDFError(f"Cannot parse or open PDF document: {exc}") from exc

        try:
            # 1. Edge Case: Encrypted / Password-protected PDF
            if doc.is_encrypted:
                raise EncryptedPDFError(
                    "Cannot compress encrypted PDF. Document requires a password."
                )

            original_page_count = len(doc)
            if original_page_count == 0:
                raise CorruptPDFError("PDF document has 0 pages")

            orig_rect = doc[0].rect
            orig_width = round(orig_rect.width)
            orig_height = round(orig_rect.height)

            # 2. Edge Case: Digital Signatures Warning
            warnings: list[str] = []
            has_signatures = doc.get_sigflags() > 0
            if has_signatures:
                warnings.append(
                    "Digital signatures detected: compressing or modifying document "
                    "structure invalidates existing cryptographic signatures."
                )

            # 3. Execution: Target-size vs Preset optimization
            if opt.target_size_bytes is not None:
                (
                    compressed_bytes,
                    strategy,
                    target_achieved,
                    target_warning,
                    meta,
                ) = PDFOptimizer.optimize_for_target_size(
                    original_bytes,
                    target_size_bytes=opt.target_size_bytes,
                    options=opt,
                )
                if target_warning:
                    warnings.append(target_warning)
            else:
                compressed_bytes, strategy, preset_warnings = PDFOptimizer.optimize_preset(
                    doc,
                    options=opt,
                )
                warnings.extend(preset_warnings)
                target_achieved = None
                meta = {
                    "strategy": strategy.value,
                    "preset": opt.preset.value,
                }

            # 4. Output validation
            validation_info = validate_pdf_output(
                compressed_bytes,
                expected_page_count=original_page_count,
            )

            meta["page_count"] = validation_info["page_count"]
            meta["has_signatures"] = has_signatures
            meta["is_form_pdf"] = validation_info["is_form_pdf"]

            combined_warning = " | ".join(warnings) if warnings else None

            return EngineResult(
                data=compressed_bytes,
                original_size=original_size,
                compressed_size=len(compressed_bytes),
                format=ImageFormat.PDF.value,
                width=validation_info["first_page_width"],
                height=validation_info["first_page_height"],
                original_width=orig_width,
                original_height=orig_height,
                target_achieved=target_achieved,
                warning=combined_warning,
                metadata=meta,
            )

        finally:
            doc.close()

    def _to_bytes(self, input_data: bytes | BinaryIO | Path) -> bytes:
        """Convert input data source to bytes."""
        if isinstance(input_data, bytes):
            return input_data
        if isinstance(input_data, Path):
            return input_data.read_bytes()
        if hasattr(input_data, "read"):
            pos = input_data.tell() if hasattr(input_data, "tell") else 0
            content = input_data.read()
            if hasattr(input_data, "seek"):
                input_data.seek(pos)
            return content
        raise ValueError(f"Unsupported input data type: {type(input_data)}")
