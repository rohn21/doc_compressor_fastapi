"""Tests for aspect-ratio resizing and transparency preservation."""

from app.engines.base import ImageFormat
from app.engines.image.strategies import (
    calculate_aspect_ratio_dimensions,
    handle_transparency,
    resize_image,
)
from PIL import Image


def test_calculate_aspect_ratio_dimensions() -> None:
    # 4000x2000 scaled down to max dimension 2000
    w, h = calculate_aspect_ratio_dimensions(4000, 2000, 2000)
    assert w == 2000
    assert h == 1000

    # Portrait 1500x3000 scaled down to max dimension 1000
    w, h = calculate_aspect_ratio_dimensions(1500, 3000, 1000)
    assert w == 500
    assert h == 1000

    # No upscaling if image is already smaller
    w, h = calculate_aspect_ratio_dimensions(800, 600, 1200, allow_upscaling=False)
    assert w == 800
    assert h == 600


def test_resize_image(sample_rgb_image: Image.Image) -> None:
    # sample_rgb_image is 800x600
    resized = resize_image(sample_rgb_image, max_dimension=400)
    assert resized.width == 400
    assert resized.height == 300


def test_transparency_handling_png(sample_rgba_image: Image.Image) -> None:
    # Preserves RGBA for PNG
    result = handle_transparency(sample_rgba_image, target_format=ImageFormat.PNG)
    assert result.mode == "RGBA"


def test_transparency_handling_webp(sample_rgba_image: Image.Image) -> None:
    # Preserves RGBA for WebP
    result = handle_transparency(sample_rgba_image, target_format=ImageFormat.WEBP)
    assert result.mode == "RGBA"


def test_transparency_handling_jpeg_flattening(sample_rgba_image: Image.Image) -> None:
    # Converts RGBA to RGB for JPEG with custom background color
    result = handle_transparency(
        sample_rgba_image,
        target_format=ImageFormat.JPEG,
        background_color=(255, 255, 255),
    )
    assert result.mode == "RGB"
    # Corners were transparent, so they must now be solid white
    assert result.getpixel((0, 0)) == (255, 255, 255)
