"""Image quality analysis and enhancement metrics using OpenCV and Pillow."""

import cv2
import numpy as np


class ImageAnalyzer:
    """Analyze image quality, blur/sharpness, and compression degradation."""

    @staticmethod
    def calculate_sharpness_score(image_bytes: bytes) -> float:
        """Calculate sharpness using Laplacian variance (higher means sharper edges)."""
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return 0.0
        return float(cv2.Laplacian(img, cv2.CV_64F).var())

    @staticmethod
    def calculate_psnr(original_bytes: bytes, compressed_bytes: bytes) -> float | None:
        """Calculate Peak Signal-to-Noise Ratio (PSNR) in dB between two images.

        Returns float in dB (typically 30-50 dB for good quality), or None if dimensions differ.
        """
        arr1 = np.frombuffer(original_bytes, np.uint8)
        arr2 = np.frombuffer(compressed_bytes, np.uint8)

        img1 = cv2.imdecode(arr1, cv2.IMREAD_COLOR)
        img2 = cv2.imdecode(arr2, cv2.IMREAD_COLOR)

        if img1 is None or img2 is None:
            return None

        # PSNR requires identical dimensions
        if img1.shape != img2.shape:
            # Resize img2 to img1 dimensions to measure perceptual fidelity
            img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]), interpolation=cv2.INTER_AREA)

        psnr_val = cv2.PSNR(img1, img2)
        return float(psnr_val)
