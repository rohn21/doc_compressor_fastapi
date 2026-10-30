"""Encoding, resizing, and transparency handling strategies for images."""

import io
from typing import Any

from PIL import Image

from app.engines.base import ImageFormat
from app.engines.image.metadata import get_icc_profile


def calculate_aspect_ratio_dimensions(
    current_width: int,
    current_height: int,
    max_dimension: int,
    allow_upscaling: bool = False,
) -> tuple[int, int]:
    """Calculate target dimensions preserving aspect ratio."""
    if current_width <= 0 or current_height <= 0 or max_dimension <= 0:
        return current_width, current_height

    largest_side = max(current_width, current_height)
    if largest_side <= max_dimension and not allow_upscaling:
        return current_width, current_height

    scale = max_dimension / float(largest_side)
    new_width = max(1, round(current_width * scale))
    new_height = max(1, round(current_height * scale))
    return new_width, new_height


def resize_image(
    img: Image.Image,
    max_dimension: int,
    allow_upscaling: bool = False,
) -> Image.Image:
    """Resize image with Lanczos resampling preserving aspect ratio."""
    target_width, target_height = calculate_aspect_ratio_dimensions(
        img.width, img.height, max_dimension, allow_upscaling
    )
    if (target_width, target_height) == (img.width, img.height):
        return img

    return img.resize((target_width, target_height), resample=Image.Resampling.LANCZOS)


def handle_transparency(
    img: Image.Image,
    target_format: ImageFormat,
    background_color: tuple[int, int, int] = (255, 255, 255),
) -> Image.Image:
    """Handle transparency safely based on target format capabilities.

    - PNG & WebP: Keep transparent RGBA/LA channels.
    - JPEG: Composite onto solid background color (default white) to prevent black artifacts.
    """
    if target_format in (ImageFormat.PNG, ImageFormat.WEBP):
        # Format supports transparency natively
        if img.mode in ("RGBA", "LA"):
            return img
        if img.mode == "P" and "transparency" in img.info:
            return img.convert("RGBA")
        return img

    # Target format does NOT support transparency (e.g. JPEG)
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        rgba = img.convert("RGBA")
        background = Image.new("RGB", rgba.size, background_color)
        # Alpha composite over solid background
        background.paste(rgba, mask=rgba.split()[3])
        return background

    if img.mode == "CMYK":
        return img.convert("RGB")

    if img.mode != "RGB" and target_format == ImageFormat.JPEG:
        return img.convert("RGB")

    return img


def encode_image(
    img: Image.Image,
    format_type: ImageFormat,
    quality: int,
    preserve_icc: bool = True,
    preserve_metadata: bool = False,
    png_compress_level: int = 9,
    png_optimize: bool = True,
) -> bytes:
    """Encode image to target format with optimized compression flags."""
    buffer = io.BytesIO()
    save_kwargs: dict[str, Any] = {}

    # Color profile preservation
    if preserve_icc:
        icc = get_icc_profile(img)
        if icc:
            save_kwargs["icc_profile"] = icc

    # EXIF preservation
    if preserve_metadata and "exif" in img.info:
        save_kwargs["exif"] = img.info["exif"]

    if format_type == ImageFormat.JPEG:
        # Standard progressive MozJPEG-style encoding
        save_kwargs["format"] = "JPEG"
        save_kwargs["quality"] = max(1, min(100, quality))
        save_kwargs["optimize"] = True
        save_kwargs["progressive"] = True
        # Standard 4:2:0 chroma subsampling for best compression
        save_kwargs["subsampling"] = 2
        img.save(buffer, **save_kwargs)

    elif format_type == ImageFormat.WEBP:
        save_kwargs["format"] = "WEBP"
        save_kwargs["quality"] = max(1, min(100, quality))
        # method=6 provides the highest compression efficiency in libwebp
        save_kwargs["method"] = 6
        img.save(buffer, **save_kwargs)

    elif format_type == ImageFormat.PNG:
        save_kwargs["format"] = "PNG"
        save_kwargs["optimize"] = png_optimize
        save_kwargs["compress_level"] = max(0, min(9, png_compress_level))
        img.save(buffer, **save_kwargs)

    else:
        raise ValueError(f"Unsupported format for encoding: {format_type}")

    return buffer.getvalue()
