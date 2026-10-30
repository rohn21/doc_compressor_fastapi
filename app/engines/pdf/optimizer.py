"""Optimization algorithms and target-size solvers for PDF documents."""

from typing import Any

import pymupdf

from app.engines.base import CompressionOptions, CompressionPreset
from app.engines.exceptions import TargetSizeUnachievableError
from app.engines.pdf.strategies import (
    PDFStrategy,
    apply_aggressive_strategy,
    apply_image_optimization_strategy,
    apply_lossless_strategy,
)


class PDFOptimizer:
    """Orchestrates PDF optimization across presets, strategies, and target-size constraints."""

    @classmethod
    def optimize_preset(
        cls,
        doc: pymupdf.Document,
        options: CompressionOptions,
    ) -> tuple[bytes, PDFStrategy, list[str]]:
        """Apply preset-driven PDF compression."""
        warnings: list[str] = []

        if options.preset == CompressionPreset.HIGH_QUALITY:
            # Lossless optimization preserves exact vector and embedded image quality
            data = apply_lossless_strategy(doc)
            return data, PDFStrategy.LOSSLESS, warnings

        if options.preset == CompressionPreset.BALANCED:
            # 200 DPI threshold, 150 DPI target, quality 80
            data = apply_image_optimization_strategy(
                doc,
                dpi_threshold=200,
                dpi_target=150,
                quality=options.quality or 80,
            )
            return data, PDFStrategy.IMAGE_OPTIMIZATION, warnings

        if options.preset == CompressionPreset.MEDIUM:
            # 150 DPI threshold, 120 DPI target, quality 68
            data = apply_image_optimization_strategy(
                doc,
                dpi_threshold=150,
                dpi_target=120,
                quality=options.quality or 68,
            )
            return data, PDFStrategy.IMAGE_OPTIMIZATION, warnings

        # Maximum Compression preset
        data, agg_warnings = apply_aggressive_strategy(
            doc,
            dpi_threshold=100,
            dpi_target=72,
            quality=options.quality or 48,
            set_to_gray=False,
        )
        warnings.extend(agg_warnings)
        return data, PDFStrategy.AGGRESSIVE, warnings

    @classmethod
    def optimize_for_target_size(
        cls,
        original_doc_bytes: bytes,
        target_size_bytes: int,
        options: CompressionOptions,
    ) -> tuple[bytes, PDFStrategy, bool, str | None, dict[str, Any]]:
        """Progressively step through compression tiers to meet target size.

        Returns (compressed_bytes, strategy, target_achieved, warning, metadata).
        """
        if target_size_bytes <= 0:
            raise ValueError(f"Target size must be positive: {target_size_bytes}")

        # Tiered candidate pipeline from highest fidelity to highest compression
        tiers = [
            ("lossless", lambda d: (apply_lossless_strategy(d), PDFStrategy.LOSSLESS, [])),
            (
                "image_150dpi",
                lambda d: (
                    apply_image_optimization_strategy(d, 200, 150, 80),
                    PDFStrategy.IMAGE_OPTIMIZATION,
                    [],
                ),
            ),
            (
                "image_120dpi",
                lambda d: (
                    apply_image_optimization_strategy(d, 150, 120, 65),
                    PDFStrategy.IMAGE_OPTIMIZATION,
                    [],
                ),
            ),
            (
                "aggressive_72dpi",
                lambda d: (
                    apply_aggressive_strategy(d, 100, 72, 50, False)[0],
                    PDFStrategy.AGGRESSIVE,
                    ["Images downsampled to 72 DPI at quality 50."],
                ),
            ),
            (
                "aggressive_grayscale",
                lambda d: (
                    apply_aggressive_strategy(d, 100, 72, 40, True)[0],
                    PDFStrategy.AGGRESSIVE,
                    ["Document converted to grayscale with 72 DPI images."],
                ),
            ),
        ]

        best_data: bytes | None = None
        best_strategy = PDFStrategy.LOSSLESS
        best_warning: str | None = None
        target_achieved = False
        last_candidate_data: bytes | None = None

        for _tier_name, tier_func in tiers:
            doc = pymupdf.open(stream=original_doc_bytes, filetype="pdf")
            try:
                candidate_data, strategy, warnings = tier_func(doc)
                last_candidate_data = candidate_data

                if len(candidate_data) <= target_size_bytes:
                    best_data = candidate_data
                    best_strategy = strategy
                    best_warning = warnings[0] if warnings else None
                    target_achieved = True
                    break
            finally:
                doc.close()

        if not target_achieved:
            best_data = last_candidate_data or original_doc_bytes
            best_strategy = PDFStrategy.AGGRESSIVE
            target_kb = round(target_size_bytes / 1024, 1)
            achieved_kb = round(len(best_data) / 1024, 1)
            best_warning = (
                f"Target size of {target_kb} KB could not be reached safely for this PDF. "
                f"Best achievable: {achieved_kb} KB."
            )

            if options.strict_target_size:
                raise TargetSizeUnachievableError(
                    best_warning,
                    details={
                        "target_bytes": target_size_bytes,
                        "achieved_bytes": len(best_data),
                    },
                )

        metadata: dict[str, Any] = {
            "target_size_bytes": target_size_bytes,
            "target_achieved": target_achieved,
            "strategy": best_strategy.value,
        }

        return best_data, best_strategy, target_achieved, best_warning, metadata
