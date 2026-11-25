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


def test_protect_report_pdf_signs_locked_free_tier_pdf_with_pades(tmp_path, monkeypatch) -> None:
    from datetime import UTC, datetime, timedelta

    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "VulnFlow Test Signer")])
    now = datetime.now(UTC)
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=5))
        .not_valid_after(now + timedelta(days=7))
        .sign(key, hashes.SHA256())
    )

    cert_file = tmp_path / "signer.crt.pem"
    key_file = tmp_path / "signer.key.pem"
    cert_file.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    key_file.write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    monkeypatch.setenv("PDF_SIGNING_CERT_PATH", str(cert_file))
    monkeypatch.setenv("PDF_SIGNING_KEY_PATH", str(key_file))

    out_bytes, sha256_hash, is_rasterized, is_signed = protect_report_pdf(
        _make_sample_pdf_bytes(), is_free_tier=True
    )

    assert is_rasterized is True
    assert is_signed is True
    assert out_bytes.lstrip().startswith(b"%PDF-")
    assert sha256_hash == hashlib.sha256(out_bytes).hexdigest()
    with pikepdf.Pdf.open(io.BytesIO(out_bytes)) as pdf:
        assert pdf.is_encrypted is True
        assert "/AcroForm" in pdf.Root
        assert str(pdf.Root.AcroForm.Fields[0].T) == "VulnFlowSeal"
