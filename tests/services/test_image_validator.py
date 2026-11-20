"""Unit tests for image magic-bytes, Pillow sanitization & SVG XSS rejection."""

import base64
import io

import pytest
from app.core.exceptions import PayloadTooLargeError, ValidationFailedError
from app.services.image_validator import validate_and_process_image
from PIL import Image


def _make_png_b64(size: tuple[int, int] = (20, 10)) -> str:
    buf = io.BytesIO()
    img = Image.new("RGBA", size, color=(200, 50, 50, 255))
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


def _make_jpeg_b64(size: tuple[int, int] = (30, 30)) -> str:
    buf = io.BytesIO()
    img = Image.new("RGB", size, color=(10, 120, 200))
    img.save(buf, format="JPEG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


def test_validate_png_with_data_uri_and_resize() -> None:
    b64 = "data:image/png;base64," + _make_png_b64((200, 100))
    data, ct, ext = validate_and_process_image(
        data_base64=b64,
        content_type="image/png",
        max_bytes=1024 * 1024,
        allow_svg=False,
        max_dimension=50,
    )
    assert ct == "image/png"
    assert ext == "png"
    with Image.open(io.BytesIO(data)) as out:
        assert max(out.size) <= 50


def test_validate_jpeg_succeeds() -> None:
    data, ct, ext = validate_and_process_image(
        data_base64=_make_jpeg_b64(),
        content_type="image/jpeg",
        max_bytes=1024 * 1024,
        allow_svg=False,
    )
    assert ct == "image/jpeg"
    assert ext == "jpg"
    assert data.startswith(b"\xff\xd8\xff")


def test_rejects_oversized_and_bad_magic_bytes() -> None:
    tiny_max_b64 = _make_png_b64((100, 100))
    with pytest.raises(PayloadTooLargeError):
        validate_and_process_image(
            data_base64=tiny_max_b64,
            content_type="image/png",
            max_bytes=10,
            allow_svg=False,
        )

    fake_png = base64.b64encode(b"MZ_NOT_A_PNG_EXECUTABLE").decode("ascii")
    with pytest.raises(ValidationFailedError):
        validate_and_process_image(
            data_base64=fake_png,
            content_type="image/png",
            max_bytes=1024,
            allow_svg=False,
        )


def test_svg_rules_and_xss_rejection() -> None:
    clean_svg = base64.b64encode(
        b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">'
        b'<rect width="10" height="10"/></svg>'
    ).decode("ascii")
    data, ct, ext = validate_and_process_image(
        data_base64=clean_svg,
        content_type="image/svg+xml",
        max_bytes=10240,
        allow_svg=True,
    )
    assert ct == "image/svg+xml"
    assert ext == "svg"
    assert b"<svg" in data

    with pytest.raises(ValidationFailedError):
        validate_and_process_image(
            data_base64=clean_svg,
            content_type="image/svg+xml",
            max_bytes=10240,
            allow_svg=False,
        )

    for payload in (
        b"<svg><script>alert(1)</script></svg>",
        b'<svg onload="alert(1)"></svg>',
        b'<svg><a href="javascript:alert(1)">x</a></svg>',
        b"<svg><foreignObject><div>hi</div></foreignObject></svg>",
    ):
        b64 = base64.b64encode(payload).decode("ascii")
        with pytest.raises(ValidationFailedError):
            validate_and_process_image(
                data_base64=b64,
                content_type="image/svg+xml",
                max_bytes=10240,
                allow_svg=True,
            )
