"""Password hashing (Argon2id) & JWT issuance/verification — PLAN.md FASE 4.2."""

import contextlib
import hashlib
import os
import secrets
import time
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError

_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except VerificationError:
        return False
    except Exception:
        return False


def get_jwt_secret_key() -> str:
    secret = os.environ.get("JWT_SECRET_KEY")
    if not secret:
        raise RuntimeError("JWT_SECRET_KEY environment variable is not set.")
    return secret


def get_jwt_algorithm() -> str:
    return os.environ.get("JWT_ALGORITHM", "HS256")


def get_jwt_expires_in_seconds() -> int:
    return int(os.environ.get("JWT_EXPIRES_IN_SECONDS", "86400"))


def create_access_token(
    *, user_id: str, token_version: int, secret_key: str, algorithm: str, expires_in_seconds: int
) -> str:
    now = int(time.time())
    payload: dict[str, Any] = {
        "sub": user_id,
        "token_version": token_version,
        "iat": now,
        "exp": now + expires_in_seconds,
    }
    return jwt.encode(payload, secret_key, algorithm=algorithm)


def decode_access_token(token: str, *, secret_key: str, algorithm: str) -> dict[str, Any]:
    return jwt.decode(token, secret_key, algorithms=[algorithm])


_INVITATION_PURPOSE = "workspace_invitation"
_INVITATION_EXPIRES_IN_SECONDS = 7 * 24 * 3600  # EC-02: 7-day invitation TTL
_used_invitation_jtis: set[str] = set()


def is_invitation_used(jti: str) -> bool:
    """F4-HIGH-11: Check if an invitation token jti has already been consumed."""
    if jti in _used_invitation_jtis:
        return True
    try:
        from app.core.redis_client import get_redis_client

        client = get_redis_client()
        return bool(client.get(f"invitation_used:{jti}"))
    except Exception:
        return False


def mark_invitation_used(jti: str, exp: int) -> None:
    """F4-HIGH-11: Mark an invitation token jti as consumed."""
    _used_invitation_jtis.add(jti)
    with contextlib.suppress(Exception):
        from app.core.redis_client import get_redis_client

        client = get_redis_client()
        ttl = max(60, exp - int(time.time()))
        client.set(f"invitation_used:{jti}", "1", ex=ttl)


def create_invitation_token(
    *, workspace_id: str, email: str = "", role: str, secret_key: str, algorithm: str
) -> str:
    """F4-HIGH-11: Bind email and unique jti to invitation token."""
    now = int(time.time())
    jti = secrets.token_urlsafe(16)
    payload: dict[str, Any] = {
        "purpose": _INVITATION_PURPOSE,
        "workspace_id": workspace_id,
        "email": email.lower(),
        "role": role,
        "jti": jti,
        "iat": now,
        "exp": now + _INVITATION_EXPIRES_IN_SECONDS,
    }
    return jwt.encode(payload, secret_key, algorithm=algorithm)


def decode_invitation_token(token: str, *, secret_key: str, algorithm: str) -> dict[str, Any]:
    payload = jwt.decode(token, secret_key, algorithms=[algorithm])
    if payload.get("purpose") != _INVITATION_PURPOSE:
        raise jwt.InvalidTokenError("Token is not a workspace invitation token.")
    jti = payload.get("jti")
    if jti and is_invitation_used(jti):
        raise jwt.InvalidTokenError("Invitation token has already been used.")
    return payload


def generate_api_key() -> tuple[str, str]:
    """Returns (raw_key, key_hash). Only key_hash (SHA-256) is persisted —
    SDD §2.4.2 #5; the raw key is shown to the user exactly once."""
    raw_key = f"vf_live_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
    return raw_key, key_hash
