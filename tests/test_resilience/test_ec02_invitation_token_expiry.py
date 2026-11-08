"""PLAN.md FASE 7.2 — EC-02: Invitation Token Expiry.

SRS UC-02 & EDGE_CASES_AND_RESILIENCE.md §6 item 2:
Workspace invitation tokens are valid for 7 days. Once expired, claims
must be rejected with AuthenticationError (HTTP 401) and prevent registration
from joining the invited workspace.
"""

import time
import uuid

import jwt
import pytest
from app.core.exceptions import AuthenticationError
from app.core.security import decode_invitation_token
from app.models.base import Base
from app.routers.auth import _join_workspace_via_invitation
from sqlalchemy import create_engine
from sqlalchemy.orm import Session


def test_ec02_decode_expired_invitation_token_raises_expired_signature() -> None:
    """An invitation token with exp in the past is rejected as expired."""
    secret = "secret-key-at-least-32-bytes-long-for-testing"
    algo = "HS256"
    now = int(time.time())

    # Build token expired 1 hour ago
    expired_payload = {
        "purpose": "workspace_invitation",
        "workspace_id": str(uuid.uuid4()),
        "email": "invitee@example.com",
        "role": "PENTESTER",
        "jti": "test-jti-expired",
        "iat": now - 3600 * 24 * 8,
        "exp": now - 3600,
    }
    expired_token = jwt.encode(expired_payload, secret, algorithm=algo)

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_invitation_token(expired_token, secret_key=secret, algorithm=algo)


def test_ec02_join_workspace_with_expired_token_raises_authentication_error(monkeypatch) -> None:
    """_join_workspace_via_invitation wraps ExpiredSignatureError in AuthenticationError."""
    secret = "secret-key-at-least-32-bytes-long-for-testing"
    monkeypatch.setenv("JWT_SECRET_KEY", secret)

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        expired_token = jwt.encode(
            {
                "purpose": "workspace_invitation",
                "workspace_id": str(uuid.uuid4()),
                "email": "invitee@example.com",
                "role": "PENTESTER",
                "iat": int(time.time()) - 1000,
                "exp": int(time.time()) - 100,
            },
            secret,
            algorithm="HS256",
        )

        with pytest.raises(AuthenticationError, match="Invitation token is invalid or expired"):
            _join_workspace_via_invitation(session, expired_token, "invitee@example.com")
    engine.dispose()
