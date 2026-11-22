"""PLAN.md FASE 4.3 — ProjectRouter (UC-06, UC-06a; EC-05 ROE validation)."""

import uuid

from app.main import app
from app.models.project import Project
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

_REGISTRATION = {
    "email": "lead@example.com",
    "password": "Str0ng!Passw0rd",
    "full_name": "Lead Pentester",
    "workspace_name": "Agensi Proyek",
}

_VALID_PROJECT = {
    "name": "Audit Bank XYZ",
    "client_name": "Bank XYZ",
    "target_scope": ["*.bankxyz.co.id", "10.20.0.0/24"],
    "roe_start_date": "2026-10-01T00:00:00Z",
    "roe_end_date": "2026-11-01T00:00:00Z",
}


def _register_and_get_token(client: TestClient) -> tuple[str, str]:
    response = client.post("/api/v1/auth/register", json=_REGISTRATION)
    body = response.json()
    return body["access_token"], body["workspace_id"]


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_create_project_persists_joined_target_scope(db_session: Session) -> None:
    with TestClient(app) as client:
        token, workspace_id = _register_and_get_token(client)
        response = client.post(
            f"/api/v1/workspaces/{workspace_id}/projects",
            json=_VALID_PROJECT,
            headers=_auth_headers(token),
        )

    assert response.status_code == 201
    body = response.json()
    assert body["target_scope"] == ["*.bankxyz.co.id", "10.20.0.0/24"]
    assert body["status"] == "ACTIVE"

    project = db_session.get(Project, uuid.UUID(body["id"]))
    assert project is not None
    assert project.target_scope == "*.bankxyz.co.id\n10.20.0.0/24"


def test_create_project_rejects_roe_end_before_start(db_session: Session) -> None:
    invalid = {
        **_VALID_PROJECT,
        "roe_start_date": "2026-11-01T00:00:00Z",
        "roe_end_date": "2026-10-01T00:00:00Z",
    }

    with TestClient(app) as client:
        token, workspace_id = _register_and_get_token(client)
        response = client.post(
            f"/api/v1/workspaces/{workspace_id}/projects",
            json=invalid,
            headers=_auth_headers(token),
        )

    assert response.status_code == 422


def test_create_project_rejects_viewer_role(db_session: Session) -> None:
    with TestClient(app) as client:
        token, workspace_id = _register_and_get_token(client)
        invite = client.post(
            f"/api/v1/workspaces/{workspace_id}/members",
            json={"email": "viewer@example.com", "role": "VIEWER"},
            headers=_auth_headers(token),
        ).json()["invitation_token"]
        viewer_token = client.post(
            "/api/v1/auth/register",
            json={
                "email": "viewer@example.com",
                "password": "Str0ng!Passw0rd",
                "full_name": "Viewer",
                "workspace_name": "Unused",
                "invitation_token": invite,
            },
        ).json()["access_token"]

        response = client.post(
            f"/api/v1/workspaces/{workspace_id}/projects",
            json=_VALID_PROJECT,
            headers=_auth_headers(viewer_token),
        )

    assert response.status_code == 403


def test_assign_lead_pentester(db_session: Session) -> None:
    with TestClient(app) as client:
        token, workspace_id = _register_and_get_token(client)
        project_id = client.post(
            f"/api/v1/workspaces/{workspace_id}/projects",
            json=_VALID_PROJECT,
            headers=_auth_headers(token),
        ).json()["id"]
        user_id = client.post(
            "/api/v1/auth/login",
            json={"email": _REGISTRATION["email"], "password": _REGISTRATION["password"]},
        ).json()["user"]["id"]

        response = client.patch(
            f"/api/v1/workspaces/{workspace_id}/projects/{project_id}/lead",
            json={"lead_pentester_id": user_id},
            headers=_auth_headers(token),
        )

    assert response.status_code == 200
    assert response.json()["lead_pentester_id"] == user_id


def test_list_projects_returns_only_this_workspaces_projects(db_session: Session) -> None:
    from app.models.subscription import Subscription

    with TestClient(app) as client:
        token, workspace_id = _register_and_get_token(client)
        sub = db_session.query(Subscription).filter_by(workspace_id=uuid.UUID(workspace_id)).one()
        sub.tier = "PRO"
        db_session.commit()

        client.post(
            f"/api/v1/workspaces/{workspace_id}/projects",
            json=_VALID_PROJECT,
            headers=_auth_headers(token),
        )
        other_workspace_id = client.post(
            "/api/v1/workspaces", json={"name": "Other"}, headers=_auth_headers(token)
        ).json()["id"]

        response = client.get(
            f"/api/v1/workspaces/{workspace_id}/projects", headers=_auth_headers(token)
        )
        other_response = client.get(
            f"/api/v1/workspaces/{other_workspace_id}/projects", headers=_auth_headers(token)
        )

    assert len(response.json()) == 1
    assert other_response.json() == []


def test_assign_lead_rejects_non_workspace_member(db_session: Session) -> None:
    # F4-HIGH-12: Assigning a lead who is not a member of the workspace returns 404
    with TestClient(app) as client:
        token, workspace_id = _register_and_get_token(client)
        project_id = client.post(
            f"/api/v1/workspaces/{workspace_id}/projects",
            json=_VALID_PROJECT,
            headers=_auth_headers(token),
        ).json()["id"]

        fake_user_id = str(uuid.uuid4())
        response = client.patch(
            f"/api/v1/workspaces/{workspace_id}/projects/{project_id}/lead",
            json={"lead_pentester_id": fake_user_id},
            headers=_auth_headers(token),
        )

    assert response.status_code == 404
    assert response.json()["code"] == "RESOURCE_NOT_FOUND"


def test_create_project_strips_newlines_from_target_scope(db_session: Session) -> None:
    # F4-LOW-23: Scope entries with newlines are stripped to prevent splitting errors
    project_with_newlines = {
        **_VALID_PROJECT,
        "target_scope": ["*.bankxyz.co.id\r\n", "  10.20.0.0/24\n  "],
    }
    with TestClient(app) as client:
        token, workspace_id = _register_and_get_token(client)
        response = client.post(
            f"/api/v1/workspaces/{workspace_id}/projects",
            json=project_with_newlines,
            headers=_auth_headers(token),
        )

    assert response.status_code == 201
    body = response.json()
    assert body["target_scope"] == ["*.bankxyz.co.id", "10.20.0.0/24"]


def test_get_update_archive_project_and_reject_viewer_as_lead(db_session: Session) -> None:
    with TestClient(app) as client:
        token, workspace_id = _register_and_get_token(client)
        headers = _auth_headers(token)
        project = client.post(
            f"/api/v1/workspaces/{workspace_id}/projects",
            json=_VALID_PROJECT,
            headers=headers,
        ).json()
        project_id = project["id"]

        fetched = client.get(
            f"/api/v1/workspaces/{workspace_id}/projects/{project_id}",
            headers=headers,
        )
        assert fetched.status_code == 200
        assert fetched.json()["name"] == "Audit Bank XYZ"

        bad_roe = client.patch(
            f"/api/v1/workspaces/{workspace_id}/projects/{project_id}",
            json={"roe_end_date": "2026-09-01T00:00:00Z"},
            headers=headers,
        )
        assert bad_roe.status_code == 422

        updated = client.patch(
            f"/api/v1/workspaces/{workspace_id}/projects/{project_id}",
            json={"name": "Audit Revised", "status": "ARCHIVED"},
            headers=headers,
        )
        assert updated.status_code == 200
        assert updated.json()["name"] == "Audit Revised"
        assert updated.json()["status"] == "ARCHIVED"

        inv = client.post(
            f"/api/v1/workspaces/{workspace_id}/members",
            headers=headers,
            json={"email": "viewer-lead@example.com", "role": "VIEWER"},
        ).json()["invitation_token"]
        viewer = client.post(
            "/api/v1/auth/register",
            json={
                "email": "viewer-lead@example.com",
                "password": "Str0ng!Passw0rd",
                "full_name": "Viewer",
                "workspace_name": "Unused",
                "invitation_token": inv,
            },
        ).json()

        lead_resp = client.patch(
            f"/api/v1/workspaces/{workspace_id}/projects/{project_id}/lead",
            json={"lead_pentester_id": viewer["user_id"]},
            headers=headers,
        )
        assert lead_resp.status_code == 422
