"""Image validation & sanitization for PoC attachments (UC-08a) & agency logos (UC-13)."""

import base64
import binascii
import io
import re

from PIL import Image, UnidentifiedImageError

from app.core.exceptions import PayloadTooLargeError, ValidationFailedError

_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
_JPEG_MAGIC = b"\xff\xd8\xff"

_SVG_DANGEROUS_PATTERN = re.compile(
    r"<\s*script\b|<\s*foreignObject\b|\bon[a-z]+\s*=|javascript\s*:|<\s*image\b[^>]*https?://",
    re.IGNORECASE,
)


def _decode_base64_image(data_base64: str) -> bytes:
    cleaned = data_base64.strip()
    if cleaned.startswith("data:") and "," in cleaned:
        _, _, cleaned = cleaned.partition(",")
    try:
        return base64.b64decode(cleaned, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValidationFailedError(f"Invalid base64 image payload: {exc}") from exc


def _sanitize_raster_image(
    raw: bytes, *, expected_format: str, max_dimension: int
) -> tuple[bytes, str, str]:
    try:
        with Image.open(io.BytesIO(raw)) as verified:
            verified.verify()
        with Image.open(io.BytesIO(raw)) as img:
            actual_format = (img.format or "").upper()
            if actual_format != expected_format:
                raise ValidationFailedError(
                    f"Image content format {actual_format!r} does not match declared type."
                )
            if max(img.size) > max_dimension:
                img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)

            output = io.BytesIO()
            if expected_format == "PNG":
                converted: Image.Image = (
                    img if img.mode in ("RGB", "RGBA", "L", "LA", "P") else img.convert("RGBA")
                )
                converted.save(output, format="PNG", optimize=True)
                return output.getvalue(), "image/png", "png"

            # JPEG has no alpha channel; flatten to RGB to strip EXIF/payloads.
            jpeg_img: Image.Image = img if img.mode == "RGB" else img.convert("RGB")
            jpeg_img.save(output, format="JPEG", quality=88, optimize=True)
            return output.getvalue(), "image/jpeg", "jpg"
    except ValidationFailedError:
        raise
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ValidationFailedError(f"Corrupt or unsupported image file: {exc}") from exc


def _validate_svg(raw: bytes) -> tuple[bytes, str, str]:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValidationFailedError("SVG file must be valid UTF-8 text.") from exc

    stripped = text.lstrip()
    if "<svg" not in stripped.lower():
        raise ValidationFailedError("Uploaded SVG does not contain an <svg> root element.")
    if _SVG_DANGEROUS_PATTERN.search(text):
        raise ValidationFailedError(
            "SVG payload contains forbidden active scripting or external image references."
        )
    return text.encode("utf-8"), "image/svg+xml", "svg"


def validate_and_process_image(
    *,
    data_base64: str,
    content_type: str,
    max_bytes: int,
    allow_svg: bool,
    max_dimension: int = 1600,
) -> tuple[bytes, str, str]:
    raw = _decode_base64_image(data_base64)
    if len(raw) > max_bytes:
        raise PayloadTooLargeError(f"Image exceeds maximum allowed size of {max_bytes} bytes.")

    if content_type == "image/png":
        if not raw.startswith(_PNG_MAGIC):
            raise ValidationFailedError("File magic bytes do not match PNG format.")
        return _sanitize_raster_image(raw, expected_format="PNG", max_dimension=max_dimension)

    if content_type == "image/jpeg":
        if not raw.startswith(_JPEG_MAGIC):
            raise ValidationFailedError("File magic bytes do not match JPEG format.")
        return _sanitize_raster_image(raw, expected_format="JPEG", max_dimension=max_dimension)

    if content_type == "image/svg+xml":
        if not allow_svg:
            raise ValidationFailedError("SVG files are not permitted for PoC attachments.")
        return _validate_svg(raw)

    raise ValidationFailedError(f"Unsupported image content type: {content_type}")
