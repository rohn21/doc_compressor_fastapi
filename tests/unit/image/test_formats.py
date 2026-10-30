"""Tests for image format detection and normalization."""

import pytest
from app.engines.base import ImageFormat
from app.engines.exceptions import UnsupportedFormatError
from app.engines.image.formats import detect_image_format, normalize_format


def test_detect_jpeg_format(sample_rgb_bytes: bytes) -> None:
    assert detect_image_format(sample_rgb_bytes) == ImageFormat.JPEG


def test_detect_png_format(sample_rgba_bytes: bytes) -> None:
    assert detect_image_format(sample_rgba_bytes) == ImageFormat.PNG


def test_detect_webp_format(sample_webp_bytes: bytes) -> None:
    assert detect_image_format(sample_webp_bytes) == ImageFormat.WEBP


def test_detect_corrupt_or_too_small() -> None:
    with pytest.raises(UnsupportedFormatError):
        detect_image_format(b"short")

    with pytest.raises(UnsupportedFormatError):
        detect_image_format(b"not-an-image-at-all-just-random-bytes-12345")


def test_normalize_format() -> None:
    assert normalize_format("image/jpeg") == ImageFormat.JPEG
    assert normalize_format("image/png") == ImageFormat.PNG
    assert normalize_format("image/webp") == ImageFormat.WEBP
    assert normalize_format(".jpg") == ImageFormat.JPEG
    assert normalize_format(".png") == ImageFormat.PNG
    assert normalize_format(".webp") == ImageFormat.WEBP
    assert normalize_format("JPEG") == ImageFormat.JPEG
    assert normalize_format(ImageFormat.JPEG) == ImageFormat.JPEG

    with pytest.raises(UnsupportedFormatError):
        normalize_format("invalid/unknown-format")
