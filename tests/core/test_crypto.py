"""Unit tests — PLAN.md FASE 2.4: helper kriptografi AES-256-GCM (SDD §2.4.3)."""

import base64

import pytest
from app.core.crypto import decrypt_poc, encrypt_poc, generate_master_key, get_encryption_key
from cryptography.exceptions import InvalidTag


def test_encrypt_poc_produces_correctly_sized_iv_and_tag() -> None:
    key = generate_master_key()

    ciphertext, iv_nonce, auth_tag = encrypt_poc(b"raw PoC evidence", key)

    assert len(iv_nonce) == 12  # SDD §2.4.3: 12-byte IV/nonce
    assert len(auth_tag) == 16  # SDD §2.4.3: 16-byte authentication tag
    assert ciphertext != b"raw PoC evidence"


def test_decrypt_poc_recovers_original_plaintext() -> None:
    key = generate_master_key()
    plaintext = b"curl -X POST http://target.internal/login -d 'admin:admin'"

    ciphertext, iv_nonce, auth_tag = encrypt_poc(plaintext, key)
    recovered = decrypt_poc(ciphertext, key, iv_nonce, auth_tag)

    assert recovered == plaintext


def test_decrypt_poc_rejects_tampered_ciphertext() -> None:
    key = generate_master_key()
    ciphertext, iv_nonce, auth_tag = encrypt_poc(b"secret evidence", key)
    tampered = bytes([ciphertext[0] ^ 0xFF]) + ciphertext[1:]

    with pytest.raises(InvalidTag):
        decrypt_poc(tampered, key, iv_nonce, auth_tag)


def test_decrypt_poc_rejects_wrong_key() -> None:
    plaintext = b"secret evidence"
    ciphertext, iv_nonce, auth_tag = encrypt_poc(plaintext, generate_master_key())

    with pytest.raises(InvalidTag):
        decrypt_poc(ciphertext, generate_master_key(), iv_nonce, auth_tag)


def test_get_encryption_key_reads_env_var(monkeypatch: pytest.MonkeyPatch) -> None:
    raw_key = generate_master_key()
    monkeypatch.setenv("ENCRYPTION_MASTER_KEY", base64.b64encode(raw_key).decode())

    assert get_encryption_key() == raw_key


def test_get_encryption_key_raises_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ENCRYPTION_MASTER_KEY", raising=False)

    with pytest.raises(RuntimeError, match="ENCRYPTION_MASTER_KEY"):
        get_encryption_key()


def test_get_encryption_key_raises_when_wrong_length(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENCRYPTION_MASTER_KEY", base64.b64encode(b"too-short").decode())

    with pytest.raises(RuntimeError, match="32 bytes"):
        get_encryption_key()
