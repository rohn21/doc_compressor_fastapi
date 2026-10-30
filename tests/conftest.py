"""Shared test fixtures for document compressor test suite."""

import io
from typing import Final

import pytest
from PIL import Image

TEST_WIDTH: Final[int] = 800
TEST_HEIGHT: Final[int] = 600


@pytest.fixture
def sample_rgb_image() -> Image.Image:
    """Generate an in-memory RGB gradient image for compression testing."""
    img = Image.new("RGB", (TEST_WIDTH, TEST_HEIGHT))
    pixels = img.load()
    assert pixels is not None
    for x in range(TEST_WIDTH):
        for y in range(TEST_HEIGHT):
            pixels[x, y] = (x % 256, y % 256, (x + y) % 256)
    return img


@pytest.fixture
def sample_rgb_bytes(sample_rgb_image: Image.Image) -> bytes:
    """Return sample RGB image encoded as JPEG bytes."""
    buf = io.BytesIO()
    sample_rgb_image.save(buf, format="JPEG", quality=95)
    return buf.getvalue()


@pytest.fixture
def sample_rgba_image() -> Image.Image:
    """Generate an in-memory RGBA image with translucent elements."""
    img = Image.new("RGBA", (400, 400), (0, 0, 0, 0))
    pixels = img.load()
    assert pixels is not None
    for x in range(100, 300):
        for y in range(100, 300):
            pixels[x, y] = (255, 0, 0, 128)  # Semi-transparent red box
    return img


@pytest.fixture
def sample_rgba_bytes(sample_rgba_image: Image.Image) -> bytes:
    """Return sample RGBA image encoded as PNG bytes."""
    buf = io.BytesIO()
    sample_rgba_image.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def sample_webp_bytes(sample_rgba_image: Image.Image) -> bytes:
    """Return sample RGBA image encoded as WebP bytes."""
    buf = io.BytesIO()
    sample_rgba_image.save(buf, format="WEBP", quality=90)
    return buf.getvalue()


@pytest.fixture
def sample_smartphone_photo_bytes() -> bytes:
    """Simulate a large 4000x3000 smartphone photo."""
    img = Image.new("RGB", (4000, 3000))
    pixels = img.load()
    assert pixels is not None
    # Add patterns so compression has real detail to work with
    for x in range(0, 4000, 50):
        for y in range(0, 3000, 50):
            pixels[x, y] = ((x * 7) % 255, (y * 13) % 255, ((x + y) * 3) % 255)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    return buf.getvalue()
