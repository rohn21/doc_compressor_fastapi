"""Tests for security guards, decompression bombs, and corruption handling."""

from unittest.mock import patch

import pytest
from app.engines.exceptions import (
    CorruptImageError,
    DecompressionBombError,
)
from app.engines.image.processor import ImageCompressionEngine
from PIL import Image


def test_compress_empty_data() -> None:
    engine = ImageCompressionEngine()
    with pytest.raises(CorruptImageError):
        engine.compress(b"")


def test_compress_corrupt_data() -> None:
    engine = ImageCompressionEngine()
    # JPEG magic bytes followed by garbage
    garbage_jpeg = b"\xff\xd8\xff\xe0" + b"\x00" * 30
    with pytest.raises(CorruptImageError):
        engine.compress(garbage_jpeg)


def test_decompression_bomb_rejection(sample_rgb_bytes: bytes) -> None:
    engine = ImageCompressionEngine()
    # Mock Image.open to return an image exceeding MAX_SAFE_PIXELS
    with patch("PIL.Image.open") as mock_open:
        mock_img = Image.new("RGB", (15000, 10000))  # 150 megapixels > 100 megapixels
        mock_open.return_value = mock_img

        with pytest.raises(DecompressionBombError):
            engine.compress(sample_rgb_bytes)
