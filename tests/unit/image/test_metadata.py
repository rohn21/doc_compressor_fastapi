"""Tests for image metadata, EXIF orientation correction, and ICC preservation."""

import io

from app.engines.image.metadata import (
    auto_orient_image,
    extract_metadata,
)
from PIL import Image


def test_auto_orient_with_exif_tags() -> None:
    # Create image with width 200, height 100
    base_img = Image.new("RGB", (200, 100), color=(255, 0, 0))

    # Add EXIF orientation tag 6 (Rotate 90 CW)
    exif = base_img.getexif()
    exif[274] = 6  # 0x0112

    buf = io.BytesIO()
    base_img.save(buf, format="JPEG", exif=exif)

    # Re-open and verify auto-orient rotates it to 100x200
    with Image.open(buf) as loaded_img:
        oriented, changed = auto_orient_image(loaded_img)
        assert changed is True
        assert oriented.width == 100
        assert oriented.height == 200


def test_extract_metadata(sample_rgb_image: Image.Image) -> None:
    meta = extract_metadata(sample_rgb_image)
    assert meta["width"] == sample_rgb_image.width
    assert meta["height"] == sample_rgb_image.height
    assert meta["mode"] == "RGB"
    assert "has_exif" in meta
