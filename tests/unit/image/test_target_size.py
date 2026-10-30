"""Tests for target-size optimization (50KB, 100KB, 200KB, 500KB, and edge cases)."""

import pytest
from app.engines.base import CompressionOptions
from app.engines.exceptions import TargetSizeUnachievableError
from app.engines.image.processor import ImageCompressionEngine


@pytest.mark.parametrize("target_kb", [50, 100, 200, 500])
def test_compress_to_standard_target_sizes(
    sample_smartphone_photo_bytes: bytes,
    target_kb: int,
) -> None:
    engine = ImageCompressionEngine()
    target_bytes = target_kb * 1024

    opts = CompressionOptions(target_size_bytes=target_bytes)
    result = engine.compress(sample_smartphone_photo_bytes, opts)

    assert result.target_achieved is True
    assert result.compressed_size <= target_bytes
    assert result.warning is None


def test_compress_target_size_unachievable_non_strict(
    sample_smartphone_photo_bytes: bytes,
) -> None:
    engine = ImageCompressionEngine()
    # Unreasonably tiny target size (500 bytes) for a 4000x3000 photo
    tiny_target = 500

    opts = CompressionOptions(
        target_size_bytes=tiny_target,
        strict_target_size=False,
    )
    result = engine.compress(sample_smartphone_photo_bytes, opts)

    # When strict=False, engine should return best safe attempt and report warning
    assert result.target_achieved is False
    assert result.warning is not None
    assert "could not be reached safely" in result.warning
    assert result.compressed_size > 0


def test_compress_target_size_unachievable_strict(
    sample_smartphone_photo_bytes: bytes,
) -> None:
    engine = ImageCompressionEngine()
    tiny_target = 500

    opts = CompressionOptions(
        target_size_bytes=tiny_target,
        strict_target_size=True,
    )

    with pytest.raises(TargetSizeUnachievableError):
        engine.compress(sample_smartphone_photo_bytes, opts)
