"""Tests for OpenCV-based image analysis and quality assessment."""

from app.engines.image.analyzer import ImageAnalyzer


def test_calculate_sharpness_score(sample_rgb_bytes: bytes) -> None:
    score = ImageAnalyzer.calculate_sharpness_score(sample_rgb_bytes)
    assert isinstance(score, float)
    assert score > 0.0


def test_calculate_psnr(sample_rgb_bytes: bytes, sample_smartphone_photo_bytes: bytes) -> None:
    # PSNR of an image with itself should be high/infinite
    psnr = ImageAnalyzer.calculate_psnr(sample_rgb_bytes, sample_rgb_bytes)
    assert psnr is not None
    assert psnr > 40.0 or psnr == float("inf")
