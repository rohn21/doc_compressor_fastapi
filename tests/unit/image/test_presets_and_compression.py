"""Tests for compression presets, smartphone photo compression, and format conversion."""

from app.engines.base import CompressionOptions, CompressionPreset, ImageFormat
from app.engines.image.processor import ImageCompressionEngine


def test_compress_smartphone_photo_with_presets(sample_smartphone_photo_bytes: bytes) -> None:
    engine = ImageCompressionEngine()

    # 1. High Quality preset (max dim 2560)
    opts_hq = CompressionOptions(preset=CompressionPreset.HIGH_QUALITY)
    res_hq = engine.compress(sample_smartphone_photo_bytes, opts_hq)

    assert res_hq.original_width == 4000
    assert res_hq.original_height == 3000
    assert max(res_hq.width, res_hq.height) == 2560
    assert res_hq.compressed_size < res_hq.original_size
    assert res_hq.saved_percentage > 0

    # 2. Balanced preset (max dim 1920)
    opts_bal = CompressionOptions(preset=CompressionPreset.BALANCED)
    res_bal = engine.compress(sample_smartphone_photo_bytes, opts_bal)
    assert max(res_bal.width, res_bal.height) == 1920
    assert res_bal.compressed_size < res_hq.compressed_size

    # 3. Medium preset (max dim 1600)
    opts_med = CompressionOptions(preset=CompressionPreset.MEDIUM)
    res_med = engine.compress(sample_smartphone_photo_bytes, opts_med)
    assert max(res_med.width, res_med.height) == 1600
    assert res_med.compressed_size < res_bal.compressed_size

    # 4. Maximum preset (max dim 1200)
    opts_max = CompressionOptions(preset=CompressionPreset.MAXIMUM)
    res_max = engine.compress(sample_smartphone_photo_bytes, opts_max)
    assert max(res_max.width, res_max.height) == 1200
    assert res_max.compressed_size < res_med.compressed_size


def test_compress_png_to_webp_conversion(sample_rgba_bytes: bytes) -> None:
    engine = ImageCompressionEngine()
    opts = CompressionOptions(
        preset=CompressionPreset.BALANCED,
        target_format=ImageFormat.WEBP,
    )
    result = engine.compress(sample_rgba_bytes, opts)

    assert result.format == ImageFormat.WEBP.value
    assert result.compressed_size > 0
    assert result.compressed_size < result.original_size


def test_compress_png_to_jpeg_conversion(sample_rgba_bytes: bytes) -> None:
    engine = ImageCompressionEngine()
    opts = CompressionOptions(
        preset=CompressionPreset.BALANCED,
        target_format=ImageFormat.JPEG,
    )
    result = engine.compress(sample_rgba_bytes, opts)

    assert result.format == ImageFormat.JPEG.value
    assert result.compressed_size > 0
