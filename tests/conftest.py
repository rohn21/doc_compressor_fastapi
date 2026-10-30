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


@pytest.fixture
def sample_text_pdf_bytes() -> bytes:
    """Generate a multi-page vector and text PDF without raster images."""
    import pymupdf

    doc = pymupdf.open()
    for i in range(3):
        page = doc.new_page(width=595, height=842)
        page.insert_text((50, 50), f"Page {i + 1} Document Title", fontsize=16)
        page.draw_rect(pymupdf.Rect(50, 100, 500, 250), color=(0, 0, 1), fill=(0.95, 0.95, 0.95))
        page.insert_textbox(
            pymupdf.Rect(60, 110, 490, 240),
            "This is a high quality vector PDF containing crisp text, vector lines, "
            "and structural elements. Compression should optimize streams without rasterizing.",
        )
    data = doc.tobytes()
    doc.close()
    return data


@pytest.fixture
def sample_image_pdf_bytes(sample_rgb_bytes: bytes) -> bytes:
    """Generate a PDF containing high-resolution embedded images."""
    import pymupdf

    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((50, 50), "Document with Embedded Photos", fontsize=14)
    # Insert image twice onto page
    page.insert_image(pymupdf.Rect(50, 100, 350, 325), stream=sample_rgb_bytes)
    page.insert_image(pymupdf.Rect(50, 350, 350, 575), stream=sample_rgb_bytes)
    data = doc.tobytes()
    doc.close()
    return data


@pytest.fixture
def sample_form_pdf_bytes() -> bytes:
    """Generate an interactive AcroForm PDF."""
    import pymupdf

    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((50, 50), "Application Form", fontsize=14)

    widget = pymupdf.Widget()
    widget.rect = pymupdf.Rect(50, 100, 250, 130)
    widget.field_name = "ApplicantName"
    widget.field_type = pymupdf.PDF_WIDGET_TYPE_TEXT
    widget.field_value = "Jane Doe"
    page.add_widget(widget)

    data = doc.tobytes()
    doc.close()
    return data


@pytest.fixture
def sample_encrypted_pdf_bytes() -> bytes:
    """Generate a password-protected encrypted PDF."""
    import pymupdf

    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((50, 50), "Confidential Protected Content")
    data = doc.tobytes(
        encryption=pymupdf.PDF_ENCRYPT_AES_256,
        user_pw="secret123",
        owner_pw="master123",
    )
    doc.close()
    return data


@pytest.fixture
def sample_signed_pdf_bytes() -> bytes:
    """Generate a PDF with digital signature widget flags."""
    import pymupdf

    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((50, 50), "Digitally Signed Contract")

    widget = pymupdf.Widget()
    widget.rect = pymupdf.Rect(50, 200, 250, 260)
    widget.field_name = "DigitalSignature"
    widget.field_type = pymupdf.PDF_WIDGET_TYPE_SIGNATURE
    page.add_widget(widget)

    data = doc.tobytes()
    doc.close()
    return data
