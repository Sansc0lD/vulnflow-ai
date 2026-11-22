"""Tamper-resistant Free-tier PDF rasterization, permissions lock, QR & PAdES signing (#7)."""

import base64
import hashlib
import io
import logging
import os
import secrets
from typing import Any

import pikepdf
import pypdfium2 as pdfium
import segno
from PIL import Image

logger = logging.getLogger("vulnflow.pdf_protector")

_CODE_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"


def generate_verification_code() -> str:
    """Generate a CSPRNG verification code (e.g. VF-XXXX-XXXX-XXXX)."""
    groups = ["".join(secrets.choice(_CODE_ALPHABET) for _ in range(4)) for _ in range(3)]
    return f"VF-{'-'.join(groups)}"


def generate_qr_png_data_uri(verify_url: str) -> str:
    """Render a PNG QR data URI (avoids emitting inline <svg> tags into PDF HTML)."""
    qr = segno.make(verify_url, error="m")
    buf = io.BytesIO()
    qr.save(buf, kind="png", scale=4, border=1, dark="#0f172a", light="#ffffff")
    encoded = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def rasterize_pdf_bytes(pdf_bytes: bytes, *, dpi: int = 180) -> bytes:
    """Flatten every PDF page into RGB raster bitmaps so watermarks cannot be stripped."""
    doc = pdfium.PdfDocument(pdf_bytes)
    scale = dpi / 72.0
    pages: list[Image.Image] = []
    try:
        for idx in range(len(doc)):
            page = doc[idx]
            try:
                bitmap = page.render(scale=scale)
                pil_img = bitmap.to_pil().convert("RGB")
                pages.append(pil_img)
            finally:
                page.close()
    finally:
        doc.close()

    if not pages:
        return pdf_bytes

    out = io.BytesIO()
    pages[0].save(
        out,
        format="PDF",
        resolution=float(dpi),
        save_all=True,
        append_images=pages[1:],
    )
    return out.getvalue()


def lock_pdf_permissions(pdf_bytes: bytes, *, owner_password: str | None = None) -> bytes:
    """Apply restrictive PDF permissions (open-readable, disallow modification/extraction)."""
    secret_owner = owner_password or secrets.token_urlsafe(24)
    out = io.BytesIO()
    with pikepdf.Pdf.open(io.BytesIO(pdf_bytes)) as pdf:
        pdf.save(
            out,
            encryption=pikepdf.Encryption(
                user="",
                owner=secret_owner,
                R=4,
                allow=pikepdf.Permissions(
                    accessibility=True,
                    extract=False,
                    modify_annotation=False,
                    modify_assembly=False,
                    modify_form=False,
                    modify_other=False,
                    print_highres=True,
                    print_lowres=True,
                ),
            ),
        )
    return out.getvalue()


def sign_pdf_pades(pdf_bytes: bytes) -> tuple[bytes, bool]:
    """Digitally certify PDF with pyHanko DocMDP (P=1) when signing cert/key env vars exist."""
    cert_path = os.environ.get("PDF_SIGNING_CERT_PATH", "").strip()
    key_path = os.environ.get("PDF_SIGNING_KEY_PATH", "").strip()
    if not cert_path or not key_path:
        return pdf_bytes, False
    if not os.path.exists(cert_path) or not os.path.exists(key_path):
        logger.warning("PDF signing paths configured but missing on disk; skipping PAdES sign.")
        return pdf_bytes, False

    passphrase_raw = os.environ.get("PDF_SIGNING_KEY_PASSPHRASE")
    passphrase = passphrase_raw.encode("utf-8") if passphrase_raw else None

    from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
    from pyhanko.sign import fields, signers

    signer: Any = signers.SimpleSigner.load(  # type: ignore[no-untyped-call]
        key_path,
        cert_path,
        key_passphrase=passphrase,
    )
    in_buf = io.BytesIO(pdf_bytes)
    writer = IncrementalPdfFileWriter(in_buf)
    meta = signers.PdfSignatureMetadata(
        field_name="VulnFlowSeal",
        md_algorithm="sha256",
        certify=True,
        docmdp_permissions=fields.MDPPerm.NO_CHANGES,
        reason="VulnFlow AI Authenticity & Integrity Seal",
    )
    out_buf = io.BytesIO()
    signers.sign_pdf(writer, meta, signer=signer, output=out_buf)
    return out_buf.getvalue(), True


def protect_report_pdf(pdf_bytes: bytes, *, is_free_tier: bool) -> tuple[bytes, str, bool, bool]:
    """Post-process rendered PDF bytes.

    Free-tier reports are rasterized into flat page images (permanently fusing
    the preview watermark into page pixels) and permission-locked, then signed
    if a signing certificate is configured. Paid reports preserve vector text and
    receive cryptographic signing + SHA-256 hash when configured.
    """
    processed = pdf_bytes
    is_rasterized = False
    is_signed = False

    looks_like_real_pdf = pdf_bytes.lstrip().startswith(b"%PDF") and len(pdf_bytes) > 64
    if is_free_tier and looks_like_real_pdf:
        processed = rasterize_pdf_bytes(processed, dpi=180)
        processed = lock_pdf_permissions(processed)
        is_rasterized = True

    if looks_like_real_pdf:
        processed, is_signed = sign_pdf_pades(processed)

    sha256_hash = hashlib.sha256(processed).hexdigest()
    return processed, sha256_hash, is_rasterized, is_signed
