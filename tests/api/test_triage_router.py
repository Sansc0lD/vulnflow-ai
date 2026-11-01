"""PLAN.md FASE 4.5 — TriageRouter (UC-09; EC-11 optimistic locking; EC-12)."""

import os
import uuid

import pytest
from app.main import app
from app.models.finding import Finding
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

_REGISTRATION = {
    "email": "triage@example.com",
    "password": "Str0ng!Passw0rd",
    "full_name": "Triage Tester",
    "workspace_name": "Agensi Triage",
}

_PROJECT = {
    "name": "Audit",
    "client_name": "Klien",
    "target_scope": ["*.klien.com"],
    "roe_start_date": "2026-10-01T00:00:00Z",
    "roe_end_date": "2026-11-01T00:00:00Z",
}

_MANUAL_FINDING = {
    "title": "Finding",
    "severity": "LOW",
    "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:N",
    "target_host": "app.klien.com",
    "proof_of_concept": {"raw_evidence": "n/a"},
}


@pytest.fixture
def ctx(db_session: Session) -> dict[str, str]:
    os.environ.setdefault("ENCRYPTION_MASTER_KEY", "9EL3Yj4ANNfiuFYY7zBoYc6XLnoD3GZpcBc6lWGLL9U=")
    with TestClient(app) as client:
        register = client.post("/api/v1/auth/register", json=_REGISTRATION).json()
        headers = {"Authorization": f"Bearer {register['access_token']}"}
        workspace_id = register["workspace_id"]
        project_id = client.post(
            f"/api/v1/workspaces/{workspace_id}/projects", json=_PROJECT, headers=headers
        ).json()["id"]
        finding_id = client.post(
            f"/api/v1/workspaces/{workspace_id}/projects/{project_id}/findings/manual",
            json=_MANUAL_FINDING,
            headers=headers,
        ).json()["id"]
    return {
        "workspace_id": workspace_id,
        "project_id": project_id,
        "finding_id": finding_id,
        "token": register["access_token"],
    }


def _status_url(ctx: dict[str, str]) -> str:
    return (
        f"/api/v1/workspaces/{ctx['workspace_id']}/projects/{ctx['project_id']}"
        f"/findings/{ctx['finding_id']}/status"
    )


def _auth(ctx: dict[str, str]) -> dict[str, str]:
    return {"Authorization": f"Bearer {ctx['token']}"}


def test_update_status_succeeds_with_correct_version(ctx: dict[str, str]) -> None:
    with TestClient(app) as client:
        response = client.patch(
            _status_url(ctx), json={"status": "IN_REVIEW", "version": 1}, headers=_auth(ctx)
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "IN_REVIEW"
    assert body["version"] == 2


def test_update_status_rejects_stale_version(ctx: dict[str, str]) -> None:
    with TestClient(app) as client:
        first = client.patch(
            _status_url(ctx), json={"status": "IN_REVIEW", "version": 1}, headers=_auth(ctx)
        )
        assert first.status_code == 200

        stale = client.patch(
            _status_url(ctx), json={"status": "REMEDIATED", "version": 1}, headers=_auth(ctx)
        )

    assert stale.status_code == 409
    assert stale.json()["code"] == "CONFLICT"


def test_update_status_to_false_positive_unchecks_curation(
    db_session: Session, ctx: dict[str, str]
) -> None:
    with TestClient(app) as client:
        response = client.patch(
            _status_url(ctx),
            json={"status": "FALSE_POSITIVE", "version": 1},
            headers=_auth(ctx),
        )

    assert response.status_code == 200
    assert response.json()["is_curated_for_report"] is False

    finding = db_session.get(Finding, uuid.UUID(ctx["finding_id"]))
    assert finding is not None
    assert finding.is_curated_for_report is False


def test_update_status_rejects_viewer_role(ctx: dict[str, str]) -> None:
    with TestClient(app) as client:
        invite = client.post(
            f"/api/v1/workspaces/{ctx['workspace_id']}/members",
            json={"email": "triage-viewer@example.com", "role": "VIEWER"},
            headers=_auth(ctx),
        ).json()["invitation_token"]
        viewer_token = client.post(
            "/api/v1/auth/register",
            json={
                "email": "triage-viewer@example.com",
                "password": "Str0ng!Passw0rd",
                "full_name": "Viewer",
                "workspace_name": "Unused",
                "invitation_token": invite,
            },
        ).json()["access_token"]

        response = client.patch(
            _status_url(ctx),
            json={"status": "IN_REVIEW", "version": 1},
            headers={"Authorization": f"Bearer {viewer_token}"},
        )

    assert response.status_code == 403


def test_update_status_rejects_unknown_finding(ctx: dict[str, str]) -> None:
    url = (
        f"/api/v1/workspaces/{ctx['workspace_id']}/projects/{ctx['project_id']}"
        f"/findings/{uuid.uuid4()}/status"
    )

    with TestClient(app) as client:
        response = client.patch(url, json={"status": "IN_REVIEW", "version": 1}, headers=_auth(ctx))

    assert response.status_code == 404


def test_update_status_rejects_cross_tenant_project_id(ctx: dict[str, str]) -> None:
    # F4-CRIT-01: Cross-tenant project_id validation in triage
    fake_project_id = str(uuid.uuid4())
    url = (
        f"/api/v1/workspaces/{ctx['workspace_id']}/projects/{fake_project_id}"
        f"/findings/{ctx['finding_id']}/status"
    )
    with TestClient(app) as client:
        response = client.patch(url, json={"status": "IN_REVIEW", "version": 1}, headers=_auth(ctx))
    assert response.status_code == 404
    assert response.json()["code"] == "RESOURCE_NOT_FOUND"
