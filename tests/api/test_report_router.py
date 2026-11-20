"""PLAN.md FASE 4.7 — ReportRouter (EC-15 double-click lock; EC-17 download proxy)."""

import os
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from app.core.redis_client import get_redis_client
from app.main import app
from app.models.report import Report
from app.routers.reports import get_report_enqueuer, get_report_storage
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

_REGISTRATION = {
    "email": "report@example.com",
    "password": "Str0ng!Passw0rd",
    "full_name": "Report Tester",
    "workspace_name": "Agensi Report",
}

_PROJECT = {
    "name": "Audit",
    "client_name": "Klien",
    "target_scope": ["*.klien.com"],
    "roe_start_date": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
    "roe_end_date": (datetime.now(UTC) + timedelta(days=30)).isoformat(),
}

_MANUAL_FINDING = {
    "title": "Finding",
    "severity": "LOW",
    "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:N",
    "target_host": "app.klien.com",
    "proof_of_concept": {"raw_evidence": "n/a"},
}


class _FakeRedis:
    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    def set(self, key: str, value: str, *, nx: bool = False, ex: int | None = None) -> bool | None:
        if nx and key in self._store:
            return None
        self._store[key] = value
        return True

    def get(self, key: str) -> str | None:
        return self._store.get(key)

    def delete(self, key: str) -> None:
        self._store.pop(key, None)


class _FakeEnqueuer:
    def __init__(self) -> None:
        self.call_count = 0

    def __call__(self, **kwargs: object) -> str:
        self.call_count += 1
        return f"job-{self.call_count}"


class _FakeStorage:
    def generate_presigned_url(self, key: str, *, expires_in_seconds: int) -> str:
        return f"https://minio.local/{key}?expires={expires_in_seconds}"


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


def _compile_url(ctx: dict[str, str]) -> str:
    return (
        f"/api/v1/workspaces/{ctx['workspace_id']}/projects/{ctx['project_id']}/reports/compile-pdf"
    )


def _auth(ctx: dict[str, str]) -> dict[str, str]:
    return {"Authorization": f"Bearer {ctx['token']}"}


@pytest.fixture(autouse=True)
def _override_infra() -> None:
    fake_redis = _FakeRedis()
    enqueuer = _FakeEnqueuer()
    app.dependency_overrides[get_redis_client] = lambda: fake_redis
    app.dependency_overrides[get_report_enqueuer] = lambda: enqueuer
    app.dependency_overrides[get_report_storage] = lambda: _FakeStorage()
    yield enqueuer
    app.dependency_overrides.pop(get_redis_client, None)
    app.dependency_overrides.pop(get_report_enqueuer, None)
    app.dependency_overrides.pop(get_report_storage, None)


def test_compile_pdf_accepts_and_returns_job_id(ctx: dict[str, str]) -> None:
    with TestClient(app) as client:
        response = client.post(
            _compile_url(ctx),
            json={"finding_ids": [ctx["finding_id"]]},
            headers=_auth(ctx),
        )

    assert response.status_code == 202
    body = response.json()
    assert body["job_id"] == "job-1"
    assert body["status"] == "QUEUED"


def test_compile_pdf_double_click_returns_same_job_id(ctx: dict[str, str]) -> None:
    # EC-15.
    with TestClient(app) as client:
        first = client.post(
            _compile_url(ctx), json={"finding_ids": [ctx["finding_id"]]}, headers=_auth(ctx)
        )
        second = client.post(
            _compile_url(ctx), json={"finding_ids": [ctx["finding_id"]]}, headers=_auth(ctx)
        )

    assert first.json()["job_id"] == second.json()["job_id"] == "job-1"


def test_compile_pdf_rejects_viewer_role(ctx: dict[str, str]) -> None:
    with TestClient(app) as client:
        invite = client.post(
            f"/api/v1/workspaces/{ctx['workspace_id']}/members",
            json={"email": "report-viewer@example.com", "role": "VIEWER"},
            headers=_auth(ctx),
        ).json()["invitation_token"]
        viewer_token = client.post(
            "/api/v1/auth/register",
            json={
                "email": "report-viewer@example.com",
                "password": "Str0ng!Passw0rd",
                "full_name": "Viewer",
                "workspace_name": "Unused",
                "invitation_token": invite,
            },
        ).json()["access_token"]

        response = client.post(
            _compile_url(ctx),
            json={"finding_ids": [ctx["finding_id"]]},
            headers={"Authorization": f"Bearer {viewer_token}"},
        )

    assert response.status_code == 403


def test_download_report_redirects_to_fresh_presigned_url(
    db_session: Session, ctx: dict[str, str]
) -> None:
    report = Report(
        project_id=uuid.UUID(ctx["project_id"]),
        report_title="Laporan",
        storage_path="reports/x/y.pdf",
        watermark_applied=False,
    )
    db_session.add(report)
    db_session.commit()

    with TestClient(app, follow_redirects=False) as client:
        response = client.get(
            f"/api/v1/workspaces/{ctx['workspace_id']}/reports/{report.id}/download",
            headers=_auth(ctx),
        )

    assert response.status_code == 307
    assert "reports/x/y.pdf" in response.headers["location"]


def test_download_unknown_report_returns_404(ctx: dict[str, str]) -> None:
    with TestClient(app) as client:
        response = client.get(
            f"/api/v1/workspaces/{ctx['workspace_id']}/reports/{uuid.uuid4()}/download",
            headers=_auth(ctx),
        )

    assert response.status_code == 404


def test_report_list_job_status_validation_and_quota_preflight(
    db_session: Session, ctx: dict[str, str]
) -> None:
    import json

    from app.models.subscription import Subscription

    fake_redis = _FakeRedis()
    app.dependency_overrides[get_redis_client] = lambda: fake_redis

    reports_url = f"/api/v1/workspaces/{ctx['workspace_id']}/projects/{ctx['project_id']}/reports"
    report = Report(
        project_id=uuid.UUID(ctx["project_id"]),
        report_title="Audit Report v1",
        version="v1.0",
        storage_path="reports/w/r.pdf",
        watermark_applied=True,
    )
    db_session.add(report)
    db_session.commit()

    with TestClient(app) as client:
        listed = client.get(reports_url, headers=_auth(ctx))
        assert listed.status_code == 200
        assert len(listed.json()) == 1
        assert listed.json()[0]["version"] == "v1.0"
        assert f"/reports/{report.id}/download" in listed.json()[0]["download_url"]

        # Malformed UUID in finding_ids rejected 422 before locking
        bad = client.post(
            _compile_url(ctx),
            json={"finding_ids": ["bad-uuid"]},
            headers=_auth(ctx),
        )
        assert bad.status_code == 422

        # Queue job and inspect job status transitions
        queued = client.post(
            _compile_url(ctx),
            json={"finding_ids": [ctx["finding_id"]]},
            headers=_auth(ctx),
        )
        assert queued.status_code == 202
        job_id = queued.json()["job_id"]
        job_url = queued.json()["status_url"]

        st_queued = client.get(job_url, headers=_auth(ctx))
        assert st_queued.status_code == 200
        assert st_queued.json()["status"] == "QUEUED"

        fake_redis.set(
            f"job:report:{job_id}",
            json.dumps(
                {
                    "job_id": job_id,
                    "workspace_id": ctx["workspace_id"],
                    "status": "COMPLETED",
                    "progress_percentage": 100,
                    "report_id": str(report.id),
                }
            ),
        )
        st_done = client.get(job_url, headers=_auth(ctx))
        assert st_done.status_code == 200
        assert st_done.json()["status"] == "COMPLETED"
        assert f"/reports/{report.id}/download" in st_done.json()["download_url"]

        fake_redis.set(
            f"job:report:{job_id}",
            json.dumps(
                {
                    "job_id": job_id,
                    "workspace_id": ctx["workspace_id"],
                    "status": "FAILED",
                    "progress_percentage": 0,
                    "error_message": "Render failed",
                }
            ),
        )
        st_fail = client.get(job_url, headers=_auth(ctx))
        assert st_fail.status_code == 200
        assert st_fail.json()["status"] == "FAILED"
        assert st_fail.json()["error_message"] == "Render failed"

        # Cross-workspace isolation returns 404
        fake_redis.set(
            f"job:report:{job_id}",
            json.dumps(
                {
                    "job_id": job_id,
                    "workspace_id": str(uuid.uuid4()),
                    "status": "QUEUED",
                    "progress_percentage": 10,
                }
            ),
        )
        assert client.get(job_url, headers=_auth(ctx)).status_code == 404

        # Quota exhausted returns 402
        sub = (
            db_session.query(Subscription)
            .filter_by(workspace_id=uuid.UUID(ctx["workspace_id"]))
            .one()
        )
        sub.reports_used_this_month = sub.monthly_report_quota
        db_session.commit()
        assert (
            client.post(
                _compile_url(ctx),
                json={"finding_ids": [ctx["finding_id"]]},
                headers=_auth(ctx),
            ).status_code
            == 402
        )


def test_download_report_json_format_returns_presigned_url_payload(
    db_session: Session, ctx: dict[str, str]
) -> None:
    report = Report(
        project_id=uuid.UUID(ctx["project_id"]),
        report_title="Laporan JSON",
        storage_path="reports/x/json.pdf",
        watermark_applied=False,
    )
    db_session.add(report)
    db_session.commit()

    with TestClient(app) as client:
        response = client.get(
            f"/api/v1/workspaces/{ctx['workspace_id']}/reports/{report.id}/download?format=json",
            headers=_auth(ctx),
        )

    assert response.status_code == 200
    body = response.json()
    assert "reports/x/json.pdf" in body["download_url"]
    assert body["expires_in_seconds"] == 900
