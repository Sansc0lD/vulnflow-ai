"""Human verification (CAPTCHA) for public Enterprise inquiries.

Supports Cloudflare Turnstile when ``TURNSTILE_SITE_KEY`` and
``TURNSTILE_SECRET_KEY`` are configured, and falls back to a built-in signed
single-use arithmetic HMAC/JWT challenge so local, beta, and air-gapped VPC
deployments remain protected without requiring external SaaS keys.
"""

from __future__ import annotations

import contextlib
import hashlib
import hmac
import os
import secrets
import time
from typing import Any, Literal

import httpx
import jwt
from redis.exceptions import RedisError

from app.core.exceptions import ValidationFailedError
from app.core.security import get_jwt_secret_key
from vulnflow_contracts import EnterpriseInquiryChallengeResponse

_CHALLENGE_TTL_SECONDS = 600
_CHALLENGE_PURPOSE = "enterprise_inquiry_captcha"
_MAX_CHALLENGE_ATTEMPTS = 3
_TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


def get_turnstile_site_key() -> str:
    return os.environ.get("TURNSTILE_SITE_KEY", "").strip()


def get_turnstile_secret_key() -> str:
    return os.environ.get("TURNSTILE_SECRET_KEY", "").strip()


def _captcha_mode() -> Literal["turnstile", "math_hmac"]:
    if get_turnstile_site_key() and get_turnstile_secret_key():
        return "turnstile"
    return "math_hmac"


def issue_inquiry_challenge() -> EnterpriseInquiryChallengeResponse:
    """Issue a new public inquiry CAPTCHA challenge."""
    if _captcha_mode() == "turnstile":
        return EnterpriseInquiryChallengeResponse(
            mode="turnstile",
            site_key=get_turnstile_site_key(),
            expires_in=_CHALLENGE_TTL_SECONDS,
        )

    a = secrets.randbelow(18) + 2
    b = secrets.randbelow(18) + 2
    if secrets.randbelow(2) == 0:
        op = "+"
        expected = a + b
    else:
        op = "-"
        if b > a:
            a, b = b, a
        expected = a - b

    now = int(time.time())
    nonce = secrets.token_hex(12)
    secret_key = get_jwt_secret_key()
    answer_mac = hmac.new(
        secret_key.encode("utf-8"),
        f"{nonce}:{expected}".encode(),
        hashlib.sha256,
    ).hexdigest()
    token = jwt.encode(
        {
            "purpose": _CHALLENGE_PURPOSE,
            "nonce": nonce,
            "mac": answer_mac,
            "iat": now,
            "exp": now + _CHALLENGE_TTL_SECONDS,
        },
        secret_key,
        algorithm="HS256",
    )
    return EnterpriseInquiryChallengeResponse(
        mode="math_hmac",
        challenge_token=token,
        prompt=f"What is {a} {op} {b}?",
        expires_in=_CHALLENGE_TTL_SECONDS,
    )


def _verify_turnstile_token(captcha_token: str | None, remote_ip: str) -> None:
    if not captcha_token or not captcha_token.strip():
        raise ValidationFailedError("Please complete the Turnstile verification challenge.")
    try:
        response = httpx.post(
            _TURNSTILE_VERIFY_URL,
            data={
                "secret": get_turnstile_secret_key(),
                "response": captcha_token.strip(),
                "remoteip": remote_ip,
            },
            timeout=5.0,
        )
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise ValidationFailedError(
            "CAPTCHA verification service unavailable. Please retry."
        ) from exc

    if not isinstance(payload, dict) or not payload.get("success"):
        raise ValidationFailedError("CAPTCHA verification failed. Please retry.")


def _consume_redis_guard(redis_client: Any | None, key: str) -> int:
    if redis_client is None:
        return 1
    try:
        count = int(redis_client.incr(key))
        if count == 1:
            redis_client.expire(key, _CHALLENGE_TTL_SECONDS)
    except (RedisError, OSError, AttributeError, ValueError):
        return 1
    return count


def _verify_math_hmac_challenge(
    captcha_token: str | None,
    captcha_answer: str | None,
    redis_client: Any | None,
) -> None:
    if not captcha_token or not captcha_answer or not captcha_answer.strip():
        raise ValidationFailedError("Please solve the security verification challenge.")

    try:
        claims = jwt.decode(
            captcha_token.strip(),
            get_jwt_secret_key(),
            algorithms=["HS256"],
        )
    except jwt.PyJWTError as exc:
        raise ValidationFailedError(
            "Verification challenge is invalid or expired. Please refresh and try again."
        ) from exc

    if claims.get("purpose") != _CHALLENGE_PURPOSE:
        raise ValidationFailedError("Verification challenge purpose mismatch.")

    nonce = str(claims.get("nonce") or "").strip()
    if not nonce:
        raise ValidationFailedError("Verification challenge is malformed.")

    if redis_client is not None:
        try:
            if redis_client.get(f"captcha:used:{nonce}") is not None:
                raise ValidationFailedError(
                    "Verification challenge was already used. Please refresh."
                )
        except (RedisError, OSError, AttributeError):
            pass

    attempts = _consume_redis_guard(redis_client, f"captcha:attempts:{nonce}")
    if attempts > _MAX_CHALLENGE_ATTEMPTS:
        raise ValidationFailedError(
            "Too many incorrect verification attempts. Please refresh the challenge."
        )

    try:
        submitted = int(captcha_answer.strip())
    except ValueError as exc:
        raise ValidationFailedError("Verification answer must be a valid number.") from exc

    expected_mac = str(claims.get("mac") or "")
    submitted_mac = hmac.new(
        get_jwt_secret_key().encode("utf-8"),
        f"{nonce}:{submitted}".encode(),
        hashlib.sha256,
    ).hexdigest()
    if not expected_mac or not hmac.compare_digest(submitted_mac, expected_mac):
        raise ValidationFailedError("Incorrect verification answer. Please try again.")

    if redis_client is not None:
        used_count = _consume_redis_guard(redis_client, f"captcha:used:{nonce}")
        if used_count > 1:
            raise ValidationFailedError("Verification challenge was already used. Please refresh.")
        with contextlib.suppress(RedisError, OSError, AttributeError):
            redis_client.set(f"captcha:used:{nonce}", "1", ex=_CHALLENGE_TTL_SECONDS)


def verify_inquiry_captcha(
    *,
    captcha_token: str | None,
    captcha_answer: str | None,
    remote_ip: str,
    redis_client: Any | None,
) -> None:
    """Validate public inquiry anti-bot verification in active mode."""
    if _captcha_mode() == "turnstile":
        _verify_turnstile_token(captcha_token, remote_ip)
        return
    _verify_math_hmac_challenge(captcha_token, captcha_answer, redis_client)
