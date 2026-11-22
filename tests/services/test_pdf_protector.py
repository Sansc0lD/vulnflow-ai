"""Unit tests for Free-tier PDF rasterization, permissions lock, QR & SHA-256 provenance."""

import hashlib
import io

import pikepdf
import pypdfium2 as pdfium
from app.services.pdf_protector import (
    generate_qr_png_data_uri,
    generate_verification_code,
    protect_report_pdf,
)
from PIL import Image, ImageDraw


def _make_sample_pdf_bytes() -> bytes:
    """Create a real 2-page PDF in memory with Pillow for rasterization tests."""
    p1 = Image.new("RGB", (595, 842), (245, 245, 245))
    draw = ImageDraw.Draw(p1)
    draw.text((40, 40), "FREE TIER PREVIEW", fill=(200, 30, 30))
    p2 = Image.new("RGB", (595, 842), (255, 255, 255))
    buf = io.BytesIO()
    p1.save(buf, format="PDF", save_all=True, append_images=[p2], resolution=72.0)
    return buf.getvalue()


def test_verification_code_and_qr_png_data_uri() -> None:
    code = generate_verification_code()
    assert code.startswith("VF-")
    assert len(code) == 17

    qr_uri = generate_qr_png_data_uri(f"https://app.vulnflow.local/verify/{code}")
    assert qr_uri.startswith("data:image/png;base64,")
    assert "<svg" not in qr_uri.lower()


def test_protect_report_pdf_rasterizes_and_locks_free_tier() -> None:
    sample_pdf = _make_sample_pdf_bytes()
    out_bytes, sha256_hash, is_rasterized, is_signed = protect_report_pdf(
        sample_pdf, is_free_tier=True
    )

    assert is_rasterized is True
    assert is_signed is False  # no PDF_SIGNING_CERT_PATH in default test env
    assert sha256_hash == hashlib.sha256(out_bytes).hexdigest()

    # Permissions encrypted with owner lock while user-openable without password
    with pikepdf.Pdf.open(io.BytesIO(out_bytes)) as pdf:
        assert len(pdf.pages) == 2
        assert pdf.is_encrypted is True
        assert pdf.allow.modify_other is False
        assert pdf.allow.extract is False
        assert pdf.allow.print_highres is True

    # Verify flattened bitmap pages contain zero strippable vector text
    doc = pdfium.PdfDocument(out_bytes)
    try:
        assert len(doc) == 2
        text_page = doc[0].get_textpage()
        assert text_page.get_text_range().strip() == ""
    finally:
        doc.close()


def test_protect_report_pdf_preserves_paid_tier_non_rasterized() -> None:
    sample_pdf = _make_sample_pdf_bytes()
    out_bytes, sha256_hash, is_rasterized, _ = protect_report_pdf(sample_pdf, is_free_tier=False)

    assert is_rasterized is False
    assert sha256_hash == hashlib.sha256(out_bytes).hexdigest()
