"""Image metadata processing, EXIF orientation correction, and ICC preservation."""

from typing import Any

from PIL import Image, ImageOps

EXIF_ORIENTATION_TAG = 274  # 0x0112


def auto_orient_image(img: Image.Image) -> tuple[Image.Image, bool]:
    """Correct image orientation based on EXIF tag (critical for smartphone photos).

    Returns the re-oriented Image and a boolean indicating whether orientation was changed.
    """
    try:
        transposed = ImageOps.exif_transpose(img)
        if transposed is not None and transposed is not img:
            return transposed, True
    except Exception:
        # If EXIF is malformed, proceed with original orientation safely
        pass
    return img, False


def extract_metadata(img: Image.Image) -> dict[str, Any]:
    """Extract metadata including EXIF tags, ICC profile, and format details."""
    metadata: dict[str, Any] = {
        "format": img.format,
        "mode": img.mode,
        "size": img.size,
        "width": img.width,
        "height": img.height,
        "has_icc_profile": "icc_profile" in img.info,
        "is_animated": getattr(img, "is_animated", False),
    }

    exif = img.getexif()
    if exif:
        metadata["has_exif"] = True
        metadata["orientation"] = exif.get(EXIF_ORIENTATION_TAG, 1)
    else:
        metadata["has_exif"] = False
        metadata["orientation"] = 1

    return metadata


def get_icc_profile(img: Image.Image) -> bytes | None:
    """Extract raw ICC color profile bytes if present."""
    return img.info.get("icc_profile")
