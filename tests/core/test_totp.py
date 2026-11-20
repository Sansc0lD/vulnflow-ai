"""Unit tests for pure-Python RFC 6238 TOTP helper — apps/api/app/core/totp.py."""

import base64

from app.core.totp import (
    build_otpauth_uri,
    compute_totp,
    generate_totp_secret,
    verify_totp,
)


def test_generate_totp_secret_is_valid_unpadded_base32() -> None:
    secret = generate_totp_secret()
    assert "=" not in secret
    assert len(secret) == 32
    decoded = base64.b32decode(secret, casefold=True)
    assert len(decoded) == 20


def test_rfc6238_sha1_known_test_vector() -> None:
    # RFC 6238 Appendix B test secret "12345678901234567890" at t=59 -> 8-digit 94287082
    secret = base64.b32encode(b"12345678901234567890").decode("ascii").rstrip("=")
    assert compute_totp(secret, for_time=59) == "287082"
    assert verify_totp(secret, "287082", for_time=59) is True


def test_verify_totp_window_and_invalid_inputs() -> None:
    secret = generate_totp_secret()
    base_time = 1_700_000_000
    code = compute_totp(secret, for_time=base_time)

    assert verify_totp(secret, code, for_time=base_time + 30, valid_window=1) is True
    assert verify_totp(secret, code, for_time=base_time - 30, valid_window=1) is True
    assert verify_totp(secret, code, for_time=base_time + 90, valid_window=1) is False
    assert verify_totp(secret, "12345", for_time=base_time) is False
    assert verify_totp(secret, "abcdef", for_time=base_time) is False
    assert verify_totp("   ", code, for_time=base_time) is False


def test_build_otpauth_uri() -> None:
    uri = build_otpauth_uri("JBSWY3DPEHPK3PXP", email="admin@vulnflow.local")
    assert uri.startswith("otpauth://totp/VulnFlow%20AI%3Aadmin%40vulnflow.local?")
    assert "secret=JBSWY3DPEHPK3PXP" in uri
    assert "digits=6" in uri
