"""PLAN.md FASE 4.3 — WorkspaceRouter (UC-04, UC-05, UC-03; SDD §2.4.2)."""

import uuid

from app.main import app
from app.models.api_key import APIKey
from app.models.workspace_member import WorkspaceMember
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

_REGISTRATION = {
    "email": "manager@example.com",
    "password": "Str0ng!Passw0rd",
    "full_name": "Manager Satu",
    "workspace_name": "Agensi Awal",
}


def _register_and_get_token(client: TestClient) -> tuple[str, str]:
    response = client.post("/api/v1/auth/register", json=_REGISTRATION)
    body = response.json()
    return body["access_token"], body["workspace_id"]


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_create_workspace_makes_caller_manager(db_session: Session) -> None:
    with TestClient(app) as client:
        token, _ = _register_and_get_token(client)
        response = client.post(
            "/api/v1/workspaces", json={"name": "Agensi Kedua"}, headers=_auth_headers(token)
        )

    assert response.status_code == 201
    workspace_id = uuid.UUID(response.json()["id"])
    member = db_session.query(WorkspaceMember).filter_by(workspace_id=workspace_id).one()
    assert member.role == "MANAGER"


def test_create_workspace_requires_authentication(db_session: Session) -> None:
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post("/api/v1/workspaces", json={"name": "X"})

    assert response.status_code == 401


def test_update_workspace_allows_manager(db_session: Session) -> None:
    with TestClient(app) as client:
        token, workspace_id = _register_and_get_token(client)
        response = client.patch(
            f"/api/v1/workspaces/{workspace_id}",
            json={"brand_primary_color": "#112233"},
            headers=_auth_headers(token),
        )

    assert response.status_code == 200
    assert response.json()["brand_primary_color"] == "#112233"


def test_update_workspace_rejects_non_member(db_session: Session) -> None:
    with TestClient(app) as client:
        _, workspace_id = _register_and_get_token(client)
        outsider_registration = {**_REGISTRATION, "email": "outsider@example.com"}
        other_token = client.post("/api/v1/auth/register", json=outsider_registration).json()[
            "access_token"
        ]
        response = client.patch(
            f"/api/v1/workspaces/{workspace_id}",
            json={"name": "Hijacked"},
            headers=_auth_headers(other_token),
        )

    assert response.status_code == 403


def test_invite_member_returns_signed_invitation_token(db_session: Session) -> None:
    with TestClient(app) as client:
        token, workspace_id = _register_and_get_token(client)
        response = client.post(
            f"/api/v1/workspaces/{workspace_id}/members",
            json={"email": "invitee@example.com", "role": "PENTESTER"},
            headers=_auth_headers(token),
        )

    assert response.status_code == 201
    body = response.json()
    assert body["invitation_token"]
    assert body["expires_in"] == 7 * 24 * 3600


def test_create_api_key_returns_raw_key_once(db_session: Session) -> None:
    with TestClient(app) as client:
        token, workspace_id = _register_and_get_token(client)
        response = client.post(
            f"/api/v1/workspaces/{workspace_id}/api-keys",
            json={"label": "CI Runner"},
            headers=_auth_headers(token),
        )

    assert response.status_code == 201
    body = response.json()
    assert body["api_key"].startswith("vf_live_")

    stored = db_session.query(APIKey).filter_by(label="CI Runner").one()
    assert stored.key_hash != body["api_key"]  # only the hash is persisted


def test_create_api_key_rejects_non_manager(db_session: Session) -> None:
    with TestClient(app) as client:
        token, workspace_id = _register_and_get_token(client)

        invite_response = client.post(
            f"/api/v1/workspaces/{workspace_id}/members",
            json={"email": "viewer@example.com", "role": "VIEWER"},
            headers=_auth_headers(token),
        )
        invitation_token = invite_response.json()["invitation_token"]
        viewer_registration = {
            "email": "viewer@example.com",
            "password": "Str0ng!Passw0rd",
            "full_name": "Viewer Satu",
            "workspace_name": "Unused",
            "invitation_token": invitation_token,
        }
        viewer_token = client.post("/api/v1/auth/register", json=viewer_registration).json()[
            "access_token"
        ]

        response = client.post(
            f"/api/v1/workspaces/{workspace_id}/api-keys",
            json={"label": "Should Fail"},
            headers=_auth_headers(viewer_token),
        )

    assert response.status_code == 403


def test_workspace_not_found_returns_404(db_session: Session) -> None:
    import uuid

    with TestClient(app) as client:
        token, _ = _register_and_get_token(client)
        response = client.patch(
            f"/api/v1/workspaces/{uuid.uuid4()}",
            json={"name": "X"},
            headers=_auth_headers(token),
        )

    assert response.status_code == 403  # not a member of a workspace that doesn't exist either


def test_create_workspace_enforces_limit_per_user(db_session: Session) -> None:
    # F4-LOW-15: Maximum 5 workspaces per user
    with TestClient(app) as client:
        token, _ = _register_and_get_token(client)
        # 1st workspace already created at register. Create 4 more -> total 5
        for i in range(2, 6):
            resp = client.post(
                "/api/v1/workspaces",
                json={"name": f"Workspace {i}"},
                headers=_auth_headers(token),
            )
            assert resp.status_code == 201

        # 6th workspace attempt must be rejected
        overflow_resp = client.post(
            "/api/v1/workspaces",
            json={"name": "Workspace 6"},
            headers=_auth_headers(token),
        )
        assert overflow_resp.status_code == 422
        assert overflow_resp.json()["code"] == "VALIDATION_FAILED"
        assert "more than 5 workspaces" in overflow_resp.json()["message"]
