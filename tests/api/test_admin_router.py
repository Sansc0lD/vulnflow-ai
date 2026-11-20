"""Superadmin TOTP MFA login & admin API tests — UC-17..19."""

from datetime import UTC, datetime, timedelta

import pytest
from app.core.redis_client import get_optional_redis_client
from app.core.security import generate_api_key
from app.core.seeder import get_seed_admin_password, get_seed_admin_totp_secret, seed_defaults
from app.core.totp import compute_totp
from app.main import app
from app.models.ai_narrative import AINarrative
from app.models.api_key import APIKey
from app.models.user import User
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


class _FakeRedis:
    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        return self._store.get(key)

    def set(self, key: str, value: str, *, ex: int | None = None) -> bool:
        self._store[key] = value
        return True


@pytest.fixture
def fake_redis() -> _FakeRedis:
    fake = _FakeRedis()
    app.dependency_overrides[get_optional_redis_client] = lambda: fake
    try:
        yield fake
    finally:
        app.dependency_overrides.pop(get_optional_redis_client, None)


def _register_regular_user(
    client: TestClient, email: str = "regular@example.com"
) -> dict[str, str]:
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "Str0ng!Passw0rd",
            "full_name": "Regular User",
            "workspace_name": f"Workspace {email}",
        },
    )
    assert resp.status_code == 201
    return resp.json()


def test_seeded_superadmin_requires_totp_mfa_and_non_superadmin_blocked(
    db_session: Session, fake_redis: _FakeRedis, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SEED_ADMIN_PASSWORD", "SeedAdmin!2026")
    monkeypatch.setenv("SEED_ADMIN_TOTP_SECRET", "JBSWY3DPEHPK3PXP")
    seed_defaults(db_session)
    admin_password = get_seed_admin_password()
    admin_secret = get_seed_admin_totp_secret()

    with TestClient(app) as client:
        regular = _register_regular_user(client)
        reg_headers = {"Authorization": f"Bearer {regular['access_token']}"}
        denied = client.get("/api/v1/admin/users", headers=reg_headers)
        assert denied.status_code == 403

        no_mfa = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@vulnflow.local", "password": admin_password},
        )
        assert no_mfa.status_code == 401
        assert no_mfa.json()["code"] == "MFA_REQUIRED"

        bad_mfa = client.post(
            "/api/v1/auth/login",
            json={
                "email": "admin@vulnflow.local",
                "password": admin_password,
                "totp_code": "000000" if compute_totp(admin_secret) != "000000" else "999999",
            },
        )
        assert bad_mfa.status_code == 401
        assert bad_mfa.json()["code"] == "AUTHENTICATION_FAILED"

        ok_mfa = client.post(
            "/api/v1/auth/login",
            json={
                "email": "admin@vulnflow.local",
                "password": admin_password,
                "totp_code": compute_totp(admin_secret),
            },
        )
        assert ok_mfa.status_code == 200
        body = ok_mfa.json()
        assert body["user"]["is_superadmin"] is True
        assert body["user"]["mfa_enabled"] is True


def test_admin_telemetry_user_governance_and_audit_logs(
    db_session: Session, fake_redis: _FakeRedis, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SEED_ADMIN_PASSWORD", "SeedAdmin!2026")
    monkeypatch.setenv("SEED_ADMIN_TOTP_SECRET", "JBSWY3DPEHPK3PXP")
    seed_defaults(db_session)
    admin_password = get_seed_admin_password()
    admin_secret = get_seed_admin_totp_secret()

    with TestClient(app) as client:
        reg = _register_regular_user(client, "target@example.com")
        reg_headers = {"Authorization": f"Bearer {reg['access_token']}"}
        target_user_id = reg["user_id"]
        target_ws_id = reg["workspace_id"]

        project_resp = client.post(
            f"/api/v1/workspaces/{target_ws_id}/projects",
            headers=reg_headers,
            json={
                "name": "Telemetry Project",
                "client_name": "Client",
                "target_scope": ["example.com"],
                "roe_start_date": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
                "roe_end_date": (datetime.now(UTC) + timedelta(days=10)).isoformat(),
            },
        )
        assert project_resp.status_code == 201
        project_id = project_resp.json()["id"]

        # Seed a raw API key owned by target user so suspend verifies revocation.
        import uuid

        _raw, key_hash = generate_api_key()
        key_row = APIKey(
            workspace_id=uuid.UUID(target_ws_id),
            created_by_user_id=uuid.UUID(target_user_id),
            key_hash=key_hash,
            label="CLI Key",
            is_active=True,
        )
        db_session.add(key_row)
        db_session.add(
            AINarrative(
                project_id=uuid.UUID(project_id),
                executive_summary="Summary",
                business_impact="Impact",
                remediation_priorities=[],
                tokens_consumed=1000,
                is_fallback=False,
            )
        )
        db_session.commit()

        admin_login = client.post(
            "/api/v1/auth/login",
            json={
                "email": "admin@vulnflow.local",
                "password": admin_password,
                "totp_code": compute_totp(admin_secret),
            },
        )
        admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

        telemetry = client.get("/api/v1/admin/telemetry/ai", headers=admin_headers)
        assert telemetry.status_code == 200
        t_data = telemetry.json()
        assert t_data["total_tokens"] == 1000
        assert t_data["total_narratives"] == 1
        assert len(t_data["by_workspace"]) == 1

        ceiling_resp = client.patch(
            "/api/v1/admin/telemetry/ai/ceiling",
            headers=admin_headers,
            json={"monthly_spend_ceiling_usd": 25.5},
        )
        assert ceiling_resp.status_code == 200
        assert ceiling_resp.json()["monthly_spend_ceiling_usd"] == 25.5

        users_resp = client.get("/api/v1/admin/users", headers=admin_headers)
        assert users_resp.status_code == 200
        assert len(users_resp.json()) >= 2

        admin_user = db_session.query(User).filter_by(email="admin@vulnflow.local").one()
        self_suspend = client.post(
            f"/api/v1/admin/users/{admin_user.id}/suspend",
            headers=admin_headers,
            json={"reason": "Self suspend attempt"},
        )
        assert self_suspend.status_code == 422

        suspend_resp = client.post(
            f"/api/v1/admin/users/{target_user_id}/suspend",
            headers=admin_headers,
            json={"reason": "Policy violation"},
        )
        assert suspend_resp.status_code == 200
        assert suspend_resp.json()["status"] == "SUSPENDED"

        # Old JWT is immediately invalidated due to token_version bump and suspended status.
        assert client.get("/api/v1/auth/me", headers=reg_headers).status_code in {401, 403}
        db_session.refresh(key_row)
        assert key_row.is_active is False

        activate_resp = client.post(
            f"/api/v1/admin/users/{target_user_id}/activate",
            headers=admin_headers,
        )
        assert activate_resp.status_code == 200
        assert activate_resp.json()["status"] == "ACTIVE"

        audits_resp = client.get(
            "/api/v1/admin/audit-logs?action=ADMIN_USER_SUSPENDED",
            headers=admin_headers,
        )
        assert audits_resp.status_code == 200
        assert audits_resp.json()["total"] == 1
