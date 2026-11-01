"""AES-256-GCM at-rest encryption helper for PoC evidence — SDD §2.4.3."""

import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

KEY_LENGTH_BYTES = 32  # AES-256
IV_LENGTH_BYTES = 12  # SDD §2.4.3: 12-byte IV/nonce
TAG_LENGTH_BYTES = 16  # SDD §2.4.3: 16-byte authentication tag


def generate_master_key() -> bytes:
    return os.urandom(KEY_LENGTH_BYTES)


def get_encryption_key() -> bytes:
    encoded = os.environ.get("ENCRYPTION_MASTER_KEY")
    if not encoded:
        raise RuntimeError("ENCRYPTION_MASTER_KEY environment variable is not set.")
    key = base64.b64decode(encoded)
    if len(key) != KEY_LENGTH_BYTES:
        raise RuntimeError(
            f"ENCRYPTION_MASTER_KEY must decode to {KEY_LENGTH_BYTES} bytes (AES-256)."
        )
    return key


def encrypt_poc(
    plaintext: bytes, key: bytes, *, associated_data: bytes | None = None
) -> tuple[bytes, bytes, bytes]:
    iv_nonce = os.urandom(IV_LENGTH_BYTES)
    ciphertext_and_tag = AESGCM(key).encrypt(iv_nonce, plaintext, associated_data)
    ciphertext, auth_tag = (
        ciphertext_and_tag[:-TAG_LENGTH_BYTES],
        ciphertext_and_tag[-TAG_LENGTH_BYTES:],
    )
    return ciphertext, iv_nonce, auth_tag


def decrypt_poc(
    ciphertext: bytes,
    key: bytes,
    iv_nonce: bytes,
    auth_tag: bytes,
    *,
    associated_data: bytes | None = None,
) -> bytes:
    return AESGCM(key).decrypt(iv_nonce, ciphertext + auth_tag, associated_data)
