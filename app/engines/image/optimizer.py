"""Optimization algorithms for image presets and target-size constraints."""

import io
from typing import Final

from PIL import Image

from app.engines.base import (
    PRESET_CONFIGS,
    CompressionOptions,
    CompressionPreset,
    ImageFormat,
)
from app.engines.exceptions import TargetSizeUnachievableError
from app.engines.image.strategies import encode_image, resize_image

MIN_SAFE_QUALITY: Final[int] = 15
MAX_SEARCH_QUALITY: Final[int] = 95
MIN_SAFE_DIMENSION: Final[int] = 320


class ImageOptimizer:
    """Optimizes image encoding parameters for presets or strict target file sizes."""

    @staticmethod
    def optimize_preset(
        img: Image.Image,
        format_type: ImageFormat,
        options: CompressionOptions,
    ) -> tuple[bytes, int, int, dict[str, int | str | bool]]:
        """Apply preset-based compression (High Quality, Balanced, Medium, Maximum)."""
        preset_cfg = PRESET_CONFIGS.get(
            options.preset,
            PRESET_CONFIGS[CompressionPreset.BALANCED],
        )

        # Allow explicit overrides from options if provided
        max_dim = options.max_dimension or preset_cfg.max_dimension
        resized_img = resize_image(img, max_dim, allow_upscaling=options.allow_upscaling)

        if format_type == ImageFormat.JPEG:
            quality = options.quality or preset_cfg.starting_quality
        elif format_type == ImageFormat.WEBP:
            quality = options.quality or preset_cfg.webp_quality
        else:
            quality = 90  # Default quality for formats that ignore quality like PNG

        data = encode_image(
            resized_img,
            format_type=format_type,
            quality=quality,
            preserve_icc=options.preserve_icc,
            preserve_metadata=options.preserve_metadata,
            png_compress_level=preset_cfg.png_compress_level,
            png_optimize=preset_cfg.png_optimize,
        )

        metadata: dict[str, int | str | bool] = {
            "preset": options.preset.value,
            "quality": quality,
            "max_dimension": max_dim,
            "width": resized_img.width,
            "height": resized_img.height,
        }

        return data, resized_img.width, resized_img.height, metadata

    @classmethod
    def optimize_for_target_size(
        cls,
        img: Image.Image,
        format_type: ImageFormat,
        target_size_bytes: int,
        options: CompressionOptions,
    ) -> tuple[bytes, int, int, bool, str | None, dict[str, int | str | bool]]:
        """Find optimal quality and scale to fit strictly within target_size_bytes.

        Uses binary search over quality combined with progressive aspect-ratio downscaling.
        Returns: (encoded_bytes, final_width, final_height, target_achieved, warning, metadata).
        """
        if target_size_bytes <= 0:
            raise ValueError(f"Invalid target size: {target_size_bytes} bytes")

        # Start with preset or options max dimension
        preset_cfg = PRESET_CONFIGS.get(
            options.preset,
            PRESET_CONFIGS[CompressionPreset.BALANCED],
        )
        current_max_dim = options.max_dimension or preset_cfg.max_dimension

        # Downscale if initial image exceeds max dimension
        working_img = resize_image(img, current_max_dim, allow_upscaling=options.allow_upscaling)

        # Handle PNG specifically (PNG compression is lossless; size is governed by
        # color depth and dimensions)
        if format_type == ImageFormat.PNG:
            return cls._optimize_png_target_size(
                working_img,
                target_size_bytes,
                options,
            )

        best_data: bytes | None = None
        best_width: int = working_img.width
        best_height: int = working_img.height
        best_quality: int = MIN_SAFE_QUALITY
        iterations = 0
        max_scale_steps = 6

        for _ in range(max_scale_steps):
            # Binary search for highest quality <= target_size_bytes
            low_q = MIN_SAFE_QUALITY
            high_q = MAX_SEARCH_QUALITY
            step_best_data: bytes | None = None
            step_best_q: int = low_q

            while low_q <= high_q:
                iterations += 1
                mid_q = (low_q + high_q) // 2

                candidate_data = encode_image(
                    working_img,
                    format_type=format_type,
                    quality=mid_q,
                    preserve_icc=options.preserve_icc,
                    preserve_metadata=options.preserve_metadata,
                )

                if len(candidate_data) <= target_size_bytes:
                    # Fits target size; try higher quality for better fidelity
                    step_best_data = candidate_data
                    step_best_q = mid_q
                    low_q = mid_q + 1
                else:
                    # Too large; reduce quality
                    high_q = mid_q - 1

            if step_best_data is not None:
                best_data = step_best_data
                best_width = working_img.width
                best_height = working_img.height
                best_quality = step_best_q
                break

            # If even lowest quality (15) is too big, downscale dimension
            largest_side = max(working_img.width, working_img.height)
            if largest_side <= MIN_SAFE_DIMENSION:
                break

            new_dim = max(MIN_SAFE_DIMENSION, int(largest_side * 0.75))
            if new_dim >= largest_side:
                break
            working_img = resize_image(working_img, new_dim)

        target_achieved = best_data is not None and len(best_data) <= target_size_bytes
        warning: str | None = None

        if not target_achieved:
            # Fallback to lowest safe quality at current dimensions
            best_data = encode_image(
                working_img,
                format_type=format_type,
                quality=MIN_SAFE_QUALITY,
                preserve_icc=options.preserve_icc,
                preserve_metadata=False,
            )
            best_width = working_img.width
            best_height = working_img.height
            best_quality = MIN_SAFE_QUALITY

            target_kb = round(target_size_bytes / 1024, 1)
            achieved_kb = round(len(best_data) / 1024, 1)
            warning = (
                f"Target size of {target_kb} KB could not be reached safely. "
                f"Best achievable without excessive degradation: {achieved_kb} KB."
            )

            if options.strict_target_size:
                raise TargetSizeUnachievableError(
                    warning,
                    details={
                        "target_bytes": target_size_bytes,
                        "achieved_bytes": len(best_data),
                    },
                )

        metadata: dict[str, int | str | bool] = {
            "quality": best_quality,
            "width": best_width,
            "height": best_height,
            "iterations": iterations,
            "target_size_bytes": target_size_bytes,
            "target_achieved": target_achieved,
        }

        return (
            best_data,
            best_width,
            best_height,
            target_achieved,
            warning,
            metadata,
        )

    @classmethod
    def _optimize_png_target_size(
        cls,
        img: Image.Image,
        target_size_bytes: int,
        options: CompressionOptions,
    ) -> tuple[bytes, int, int, bool, str | None, dict[str, int | str | bool]]:
        """PNG target-size optimization via scaling and adaptive palette quantization."""
        working_img = img
        iterations = 0
        best_data: bytes | None = None
        max_scale_steps = 6

        for _ in range(max_scale_steps):
            iterations += 1
            # Try lossless PNG encoding first
            candidate = encode_image(
                working_img,
                format_type=ImageFormat.PNG,
                quality=100,
                preserve_icc=options.preserve_icc,
                preserve_metadata=options.preserve_metadata,
                png_compress_level=9,
                png_optimize=True,
            )

            if len(candidate) <= target_size_bytes:
                best_data = candidate
                break

            # Try 8-bit adaptive quantization if RGBA/RGB
            if working_img.mode in ("RGBA", "RGB"):
                iterations += 1
                try:
                    quantized = working_img.quantize(colors=256, method=Image.Quantize.MEDIANCUT)
                    buf = io.BytesIO()
                    quantized.save(buf, format="PNG", optimize=True, compress_level=9)
                    q_data = buf.getvalue()
                    if len(q_data) <= target_size_bytes:
                        best_data = q_data
                        break
                except Exception:
                    pass

            largest_side = max(working_img.width, working_img.height)
            if largest_side <= MIN_SAFE_DIMENSION:
                break

            new_dim = max(MIN_SAFE_DIMENSION, int(largest_side * 0.75))
            if new_dim >= largest_side:
                break
            working_img = resize_image(working_img, new_dim)

        target_achieved = best_data is not None and len(best_data) <= target_size_bytes
        warning: str | None = None

        if not target_achieved:
            best_data = encode_image(
                working_img,
                format_type=ImageFormat.PNG,
                quality=100,
                preserve_icc=options.preserve_icc,
                preserve_metadata=False,
                png_compress_level=9,
                png_optimize=True,
            )
            target_kb = round(target_size_bytes / 1024, 1)
            achieved_kb = round(len(best_data) / 1024, 1)
            warning = (
                f"PNG target size of {target_kb} KB could not be reached safely. "
                f"Best achievable: {achieved_kb} KB."
            )
            if options.strict_target_size:
                raise TargetSizeUnachievableError(
                    warning,
                    details={
                        "target_bytes": target_size_bytes,
                        "achieved_bytes": len(best_data),
                    },
                )

        metadata: dict[str, int | str | bool] = {
            "width": working_img.width,
            "height": working_img.height,
            "iterations": iterations,
            "target_size_bytes": target_size_bytes,
            "target_achieved": target_achieved,
        }

        return (
            best_data,
            working_img.width,
            working_img.height,
            target_achieved,
            warning,
            metadata,
        )
