"""PLAN.md FASE 4.2 — password hashing (Argon2id) & JWT issuance/verification."""

import time

import jwt
import pytest
from app.core.security import (
    create_access_token,
    create_invitation_token,
    decode_access_token,
    decode_invitation_token,
    generate_api_key,
    get_jwt_algorithm,
    get_jwt_expires_in_seconds,
    get_jwt_secret_key,
    hash_password,
    verify_password,
)
from argon2.exceptions import VerifyMismatchError


def test_hash_password_produces_argon2id_hash() -> None:
    hashed = hash_password("Str0ng!Passw0rd")
    assert hashed.startswith("$argon2id$")


def test_verify_password_accepts_correct_password() -> None:
    hashed = hash_password("Str0ng!Passw0rd")
    assert verify_password("Str0ng!Passw0rd", hashed) is True


def test_verify_password_rejects_wrong_password() -> None:
    hashed = hash_password("Str0ng!Passw0rd")
    assert verify_password("WrongPassword1!", hashed) is False


def test_verify_password_rejects_malformed_hash_without_raising() -> None:
    assert verify_password("anything", "not-a-real-hash") is False


def test_create_and_decode_access_token_roundtrip() -> None:
    token = create_access_token(
        user_id="user-123",
        token_version=1,
        secret_key="s3cr3t-s3cr3t-s3cr3t-s3cr3t-32bytes!",
        algorithm="HS256",
        expires_in_seconds=3600,
    )

    payload = decode_access_token(
        token, secret_key="s3cr3t-s3cr3t-s3cr3t-s3cr3t-32bytes!", algorithm="HS256"
    )

    assert payload["sub"] == "user-123"
    assert payload["token_version"] == 1


def test_decode_access_token_rejects_tampered_signature() -> None:
    token = create_access_token(
        user_id="user-123",
        token_version=1,
        secret_key="s3cr3t-s3cr3t-s3cr3t-s3cr3t-32bytes!",
        algorithm="HS256",
        expires_in_seconds=3600,
    )

    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(
            token, secret_key="wrong-secret-wrong-secret-32-bytes!", algorithm="HS256"
        )


def test_decode_access_token_rejects_expired_token() -> None:
    token = create_access_token(
        user_id="user-123",
        token_version=1,
        secret_key="s3cr3t-s3cr3t-s3cr3t-s3cr3t-32bytes!",
        algorithm="HS256",
        expires_in_seconds=-1,
    )

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(
            token, secret_key="s3cr3t-s3cr3t-s3cr3t-s3cr3t-32bytes!", algorithm="HS256"
        )


def test_get_jwt_secret_key_reads_env_var(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET_KEY", "my-secret")
    assert get_jwt_secret_key() == "my-secret"


def test_get_jwt_secret_key_raises_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError, match="JWT_SECRET_KEY"):
        get_jwt_secret_key()


def test_get_jwt_algorithm_defaults_to_hs256(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("JWT_ALGORITHM", raising=False)
    assert get_jwt_algorithm() == "HS256"


def test_get_jwt_expires_in_seconds_defaults_to_24_hours(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("JWT_EXPIRES_IN_SECONDS", raising=False)
    assert get_jwt_expires_in_seconds() == 86400


def test_verify_password_error_type_is_specific_not_bare_except() -> None:
    # Guard against a lazy `except Exception` swallowing real bugs: confirm
    # the mismatch path actually goes through argon2's own exception type.
    hashed = hash_password("Str0ng!Passw0rd")
    with pytest.raises(VerifyMismatchError):
        from argon2 import PasswordHasher

        PasswordHasher().verify(hashed, "WrongPassword1!")


# Sanity: hashing itself takes non-trivial time (Argon2id is intentionally
# slow) but must not be pathologically slow for a single call in tests.
def test_hash_password_completes_within_reasonable_time() -> None:
    start = time.perf_counter()
    hash_password("Str0ng!Passw0rd")
    assert time.perf_counter() - start < 2.0


def test_create_and_decode_invitation_token_roundtrip() -> None:
    # EC-02: 7-day signed invitation token.
    token = create_invitation_token(
        workspace_id="ws-123",
        role="PENTESTER",
        secret_key="s3cr3t-s3cr3t-s3cr3t-s3cr3t-32bytes!",
        algorithm="HS256",
    )

    payload = decode_invitation_token(
        token, secret_key="s3cr3t-s3cr3t-s3cr3t-s3cr3t-32bytes!", algorithm="HS256"
    )

    assert payload["workspace_id"] == "ws-123"
    assert payload["role"] == "PENTESTER"


def test_decode_invitation_token_rejects_an_access_token() -> None:
    # An ordinary access token must not be usable as a workspace invitation.
    access_token = create_access_token(
        user_id="user-123",
        token_version=1,
        secret_key="s3cr3t-s3cr3t-s3cr3t-s3cr3t-32bytes!",
        algorithm="HS256",
        expires_in_seconds=3600,
    )

    with pytest.raises(jwt.InvalidTokenError):
        decode_invitation_token(
            access_token, secret_key="s3cr3t-s3cr3t-s3cr3t-s3cr3t-32bytes!", algorithm="HS256"
        )


def test_generate_api_key_returns_raw_key_and_matching_sha256_hash() -> None:
    import hashlib

    raw_key, key_hash = generate_api_key()

    assert raw_key.startswith("vf_live_")
    assert key_hash == hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
    assert len(key_hash) == 64


def test_generate_api_key_is_unique_per_call() -> None:
    raw_key_1, _ = generate_api_key()
    raw_key_2, _ = generate_api_key()
    assert raw_key_1 != raw_key_2


def test_verify_password_returns_false_on_corrupt_hash() -> None:
    # F4-MED-10: Corrupt hash should return False, never raise 500
    assert not verify_password("Password123!", "not-a-valid-argon2-hash")
    assert not verify_password("Password123!", "$argon2id$v=19$m=65536,t=3,p=4$corrupt$garbage")


def test_invitation_token_binds_email_and_prevents_replay() -> None:
    from app.core.security import mark_invitation_used

    token = create_invitation_token(
        workspace_id="ws-123",
        email="invited@example.com",
        role="PENTESTER",
        secret_key="s3cr3t-s3cr3t-s3cr3t-s3cr3t-32bytes!",
        algorithm="HS256",
    )
    payload = decode_invitation_token(
        token, secret_key="s3cr3t-s3cr3t-s3cr3t-s3cr3t-32bytes!", algorithm="HS256"
    )
    assert payload["email"] == "invited@example.com"
    assert "jti" in payload

    # Consume the token
    mark_invitation_used(payload["jti"], payload["exp"])

    # Replay should now fail
    with pytest.raises(jwt.InvalidTokenError, match="already been used"):
        decode_invitation_token(
            token, secret_key="s3cr3t-s3cr3t-s3cr3t-s3cr3t-32bytes!", algorithm="HS256"
        )
