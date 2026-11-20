"""RFC 6238 TOTP (6-digit, 30s step, HMAC-SHA1) using pure Python stdlib."""

import base64
import hashlib
import hmac
import secrets
import struct
import time
import urllib.parse


def generate_totp_secret() -> str:
    """Generate a 160-bit Base32 secret (unpadded) compatible with authenticator apps."""
    return base64.b32encode(secrets.token_bytes(20)).decode("ascii").rstrip("=")


def _decode_base32_secret(secret: str) -> bytes:
    cleaned = secret.strip().replace(" ", "").upper()
    if not cleaned:
        raise ValueError("TOTP secret must not be empty.")
    padding = (-len(cleaned)) % 8
    return base64.b32decode(cleaned + ("=" * padding), casefold=True)


def compute_totp(
    secret: str, *, for_time: int | None = None, step_seconds: int = 30, digits: int = 6
) -> str:
    key = _decode_base32_secret(secret)
    timestamp = int(time.time()) if for_time is None else int(for_time)
    counter = timestamp // step_seconds
    counter_bytes = struct.pack(">Q", counter)
    digest = hmac.new(key, counter_bytes, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code_int = (struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF) % (10**digits)
    return f"{code_int:0{digits}d}"


def verify_totp(
    secret: str,
    code: str,
    *,
    for_time: int | None = None,
    valid_window: int = 1,
    step_seconds: int = 30,
) -> bool:
    normalized = code.strip()
    if len(normalized) != 6 or not normalized.isdigit():
        return False
    base_time = int(time.time()) if for_time is None else int(for_time)
    try:
        for delta in range(-valid_window, valid_window + 1):
            expected = compute_totp(
                secret, for_time=base_time + (delta * step_seconds), step_seconds=step_seconds
            )
            if hmac.compare_digest(expected, normalized):
                return True
    except ValueError:
        return False
    return False


def build_otpauth_uri(secret: str, *, email: str, issuer: str = "VulnFlow AI") -> str:
    label = urllib.parse.quote(f"{issuer}:{email}")
    params = urllib.parse.urlencode({"secret": secret, "issuer": issuer, "digits": "6"})
    return f"otpauth://totp/{label}?{params}"
