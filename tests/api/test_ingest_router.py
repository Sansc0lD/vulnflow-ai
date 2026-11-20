"""PLAN.md FASE 4.4 — IngestRouter (SDD §2.6.1.2; EC-04/EC-08/EC-09/EC-10)."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from app.core.redis_client import get_redis_client_factory
from app.main import app
from app.models.finding import Finding
from app.models.proof_of_concept import ProofOfConcept
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


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


_REGISTRATION = {
    "email": "ingest@example.com",
    "password": "Str0ng!Passw0rd",
    "full_name": "Ingest Tester",
    "workspace_name": "Agensi Ingest",
}

_PROJECT = {
    "name": "Audit",
    "client_name": "Klien",
    "target_scope": ["*.klien.com"],
    "roe_start_date": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
    "roe_end_date": (datetime.now(UTC) + timedelta(days=30)).isoformat(),
}


def _one_finding(**overrides: object) -> dict[str, object]:
    base = {
        "title": "SQL Injection",
        "severity": "CRITICAL",
        "cvss_version": "3.1",
        "cvss_score": 9.8,
        "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
        "cwe_id": "CWE-89",
        "target_host": "app.klien.com",
        "target_port": 443,
        "protocol": "https",
        "source_tool": "nuclei",
        "proof_of_concept": {"raw_evidence": "' OR 1=1--"},
    }
    return {**base, **overrides}


@pytest.fixture
def workspace_project_and_api_key(db_session: Session) -> dict[str, str]:
    import os

    os.environ.setdefault("ENCRYPTION_MASTER_KEY", "9EL3Yj4ANNfiuFYY7zBoYc6XLnoD3GZpcBc6lWGLL9U=")
    with TestClient(app) as client:
        register = client.post("/api/v1/auth/register", json=_REGISTRATION).json()
        token = register["access_token"]
        workspace_id = register["workspace_id"]
        headers = {"Authorization": f"Bearer {token}"}
        project_id = client.post(
            f"/api/v1/workspaces/{workspace_id}/projects", json=_PROJECT, headers=headers
        ).json()["id"]
        api_key = client.post(
            f"/api/v1/workspaces/{workspace_id}/api-keys",
            json={"label": "CLI"},
            headers=headers,
        ).json()["api_key"]
    return {"workspace_id": workspace_id, "project_id": project_id, "api_key": api_key}


def _batch_url(ctx: dict[str, str]) -> str:
    return f"/api/v1/workspaces/{ctx['workspace_id']}/projects/{ctx['project_id']}/findings/batch"


def test_batch_ingest_creates_finding_and_encrypts_poc(
    db_session: Session, workspace_project_and_api_key: dict[str, str]
) -> None:
    ctx = workspace_project_and_api_key
    payload = {
        "scan_metadata": {
            "scanner_name": "nuclei",
            "scanner_version": "v3.2.4",
            "scan_duration_seconds": 1.5,
        },
        "findings": [_one_finding()],
    }

    with TestClient(app) as client:
        response = client.post(
            _batch_url(ctx), json=payload, headers={"X-VulnFlow-API-Key": ctx["api_key"]}
        )

    assert response.status_code == 201
    body = response.json()
    assert body == {
        "new_findings_count": 1,
        "duplicate_findings_count": 0,
        "quarantined_count": 0,
        "reopened_findings_count": 0,
    }

    finding = db_session.query(Finding).filter_by(project_id=uuid.UUID(ctx["project_id"])).one()
    poc = db_session.query(ProofOfConcept).filter_by(finding_id=finding.id).one()
    assert poc.encrypted_raw_evidence != b"' OR 1=1--"  # stored encrypted, not plaintext


def test_batch_ingest_deduplicates_identical_findings(
    db_session: Session, workspace_project_and_api_key: dict[str, str]
) -> None:
    ctx = workspace_project_and_api_key
    payload = {
        "scan_metadata": {
            "scanner_name": "nuclei",
            "scanner_version": "v3",
            "scan_duration_seconds": 1,
        },
        "findings": [_one_finding(), _one_finding()],
    }

    with TestClient(app) as client:
        response = client.post(
            _batch_url(ctx), json=payload, headers={"X-VulnFlow-API-Key": ctx["api_key"]}
        )

    assert response.json() == {
        "new_findings_count": 1,
        "duplicate_findings_count": 1,
        "quarantined_count": 0,
        "reopened_findings_count": 0,
    }


def test_batch_ingest_quarantines_out_of_scope_finding(
    db_session: Session, workspace_project_and_api_key: dict[str, str]
) -> None:
    ctx = workspace_project_and_api_key
    payload = {
        "scan_metadata": {
            "scanner_name": "nuclei",
            "scanner_version": "v3",
            "scan_duration_seconds": 1,
        },
        "findings": [_one_finding(target_host="evil.other.com")],
    }

    with TestClient(app) as client:
        response = client.post(
            _batch_url(ctx), json=payload, headers={"X-VulnFlow-API-Key": ctx["api_key"]}
        )

    assert response.json()["quarantined_count"] == 1
    finding = db_session.query(Finding).filter_by(target_host="evil.other.com").one()
    assert finding.is_quarantined is True


def test_batch_ingest_accepts_null_port_finding(
    db_session: Session, workspace_project_and_api_key: dict[str, str]
) -> None:
    ctx = workspace_project_and_api_key
    payload = {
        "scan_metadata": {
            "scanner_name": "manual",
            "scanner_version": "v1",
            "scan_duration_seconds": 0,
        },
        "findings": [_one_finding(target_port=None, source_tool="manual")],
    }

    with TestClient(app) as client:
        response = client.post(
            _batch_url(ctx), json=payload, headers={"X-VulnFlow-API-Key": ctx["api_key"]}
        )

    assert response.status_code == 201
    finding = db_session.query(Finding).filter_by(project_id=uuid.UUID(ctx["project_id"])).one()
    assert finding.target_port is None


def test_batch_ingest_computes_score_from_vector_when_score_omitted(
    db_session: Session, workspace_project_and_api_key: dict[str, str]
) -> None:
    ctx = workspace_project_and_api_key
    finding = _one_finding()
    del finding["cvss_score"]
    payload = {
        "scan_metadata": {
            "scanner_name": "nuclei",
            "scanner_version": "v3",
            "scan_duration_seconds": 1,
        },
        "findings": [finding],
    }

    with TestClient(app) as client:
        response = client.post(
            _batch_url(ctx), json=payload, headers={"X-VulnFlow-API-Key": ctx["api_key"]}
        )

    assert response.status_code == 201
    stored = db_session.query(Finding).filter_by(project_id=uuid.UUID(ctx["project_id"])).one()
    assert float(stored.cvss_score) == 9.8  # same vector as test_batch_ingest_creates_finding...


def test_batch_ingest_rejects_over_free_tier_limit(
    db_session: Session, workspace_project_and_api_key: dict[str, str]
) -> None:
    ctx = workspace_project_and_api_key
    findings = [_one_finding(endpoint_path=f"/path-{i}") for i in range(51)]
    payload = {
        "scan_metadata": {
            "scanner_name": "nuclei",
            "scanner_version": "v3",
            "scan_duration_seconds": 1,
        },
        "findings": findings,
    }

    with TestClient(app) as client:
        response = client.post(
            _batch_url(ctx), json=payload, headers={"X-VulnFlow-API-Key": ctx["api_key"]}
        )

    assert response.status_code == 413
    assert response.json()["code"] == "BATCH_LIMIT_EXCEEDED"


def test_batch_ingest_rejects_missing_api_key(
    db_session: Session, workspace_project_and_api_key: dict[str, str]
) -> None:
    ctx = workspace_project_and_api_key
    payload = {
        "scan_metadata": {
            "scanner_name": "nuclei",
            "scanner_version": "v3",
            "scan_duration_seconds": 1,
        },
        "findings": [_one_finding()],
    }

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post(_batch_url(ctx), json=payload)

    assert response.status_code == 401


def test_manual_finding_computes_score_from_vector(
    db_session: Session, workspace_project_and_api_key: dict[str, str]
) -> None:
    ctx = workspace_project_and_api_key
    payload = {
        "title": "Manually Found XSS",
        "severity": "HIGH",
        "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
        "cwe_id": "CWE-79",
        "target_host": "app.klien.com",
        "proof_of_concept": {"raw_evidence": "<script>alert(1)</script>"},
    }

    with TestClient(app) as client:
        # workspace/project were already created by the fixture; log back in
        # as that same manager to get a fresh token for this test's client.
        login = client.post(
            "/api/v1/auth/login",
            json={"email": _REGISTRATION["email"], "password": _REGISTRATION["password"]},
        ).json()
        token = login["access_token"]
        response = client.post(
            f"/api/v1/workspaces/{ctx['workspace_id']}/projects/{ctx['project_id']}/findings/manual",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 201
    body = response.json()
    assert body["cvss_score"] == 9.8
    assert body["source_tool"] == "manual"
    assert body["status"] == "OPEN"


def test_manual_finding_rejects_viewer_role(
    db_session: Session, workspace_project_and_api_key: dict[str, str]
) -> None:
    ctx = workspace_project_and_api_key
    payload = {
        "title": "X",
        "severity": "LOW",
        "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:N",
        "target_host": "app.klien.com",
        "proof_of_concept": {"raw_evidence": "n/a"},
    }

    with TestClient(app) as client:
        login = client.post(
            "/api/v1/auth/login",
            json={"email": _REGISTRATION["email"], "password": _REGISTRATION["password"]},
        ).json()
        manager_token = login["access_token"]
        invite = client.post(
            f"/api/v1/workspaces/{ctx['workspace_id']}/members",
            json={"email": "manual-viewer@example.com", "role": "VIEWER"},
            headers={"Authorization": f"Bearer {manager_token}"},
        ).json()["invitation_token"]
        viewer_token = client.post(
            "/api/v1/auth/register",
            json={
                "email": "manual-viewer@example.com",
                "password": "Str0ng!Passw0rd",
                "full_name": "Viewer",
                "workspace_name": "Unused",
                "invitation_token": invite,
            },
        ).json()["access_token"]

        response = client.post(
            f"/api/v1/workspaces/{ctx['workspace_id']}/projects/{ctx['project_id']}/findings/manual",
            json=payload,
            headers={"Authorization": f"Bearer {viewer_token}"},
        )

    assert response.status_code == 403


def test_batch_ingest_idempotency_key_short_circuits_reprocessing(
    db_session: Session, workspace_project_and_api_key: dict[str, str]
) -> None:
    # EC-07: a retried request carrying the SAME Idempotency-Key must get
    # back the exact result of the original attempt without reprocessing —
    # proven here by sending a *different* finding on the second call. If
    # the gate works, that second finding is never persisted and the
    # response is byte-identical to the first. (dedup_hash alone would not
    # produce this: it dedups by finding content, not by request identity,
    # so a genuinely different finding would normally always be accepted.)
    ctx = workspace_project_and_api_key
    fake_redis = _FakeRedis()
    app.dependency_overrides[get_redis_client_factory] = lambda: lambda: fake_redis
    try:
        headers = {"X-VulnFlow-API-Key": ctx["api_key"], "Idempotency-Key": "chunk-0"}
        scan_metadata = {
            "scanner_name": "nuclei",
            "scanner_version": "v3",
            "scan_duration_seconds": 1,
        }

        with TestClient(app) as client:
            first = client.post(
                _batch_url(ctx),
                json={"scan_metadata": scan_metadata, "findings": [_one_finding()]},
                headers=headers,
            )
            second = client.post(
                _batch_url(ctx),
                json={
                    "scan_metadata": scan_metadata,
                    "findings": [_one_finding(endpoint_path="/totally-different-finding")],
                },
                headers=headers,
            )

        assert first.status_code == second.status_code == 201
        assert (
            first.json()
            == second.json()
            == {
                "new_findings_count": 1,
                "duplicate_findings_count": 0,
                "quarantined_count": 0,
                "reopened_findings_count": 0,
            }
        )
        all_findings = (
            db_session.query(Finding).filter_by(project_id=uuid.UUID(ctx["project_id"])).all()
        )
        assert len(all_findings) == 1  # the second call's finding was never persisted
    finally:
        app.dependency_overrides.pop(get_redis_client_factory, None)


def test_batch_ingest_different_idempotency_keys_both_process(
    db_session: Session, workspace_project_and_api_key: dict[str, str]
) -> None:
    # EC-07's other half: distinct keys (one per chunk) must NOT be treated
    # as replays of each other.
    ctx = workspace_project_and_api_key
    fake_redis = _FakeRedis()
    app.dependency_overrides[get_redis_client_factory] = lambda: lambda: fake_redis
    try:
        scan_metadata = {
            "scanner_name": "nuclei",
            "scanner_version": "v3",
            "scan_duration_seconds": 1,
        }
        with TestClient(app) as client:
            first = client.post(
                _batch_url(ctx),
                json={"scan_metadata": scan_metadata, "findings": [_one_finding()]},
                headers={"X-VulnFlow-API-Key": ctx["api_key"], "Idempotency-Key": "chunk-0"},
            )
            second = client.post(
                _batch_url(ctx),
                json={
                    "scan_metadata": scan_metadata,
                    "findings": [_one_finding(endpoint_path="/chunk-1-finding")],
                },
                headers={"X-VulnFlow-API-Key": ctx["api_key"], "Idempotency-Key": "chunk-1"},
            )

        assert first.json()["new_findings_count"] == 1
        assert second.json()["new_findings_count"] == 1
        all_findings = (
            db_session.query(Finding).filter_by(project_id=uuid.UUID(ctx["project_id"])).all()
        )
        assert len(all_findings) == 2
    finally:
        app.dependency_overrides.pop(get_redis_client_factory, None)


def test_batch_ingest_rejects_api_key_for_different_workspace(
    db_session: Session, workspace_project_and_api_key: dict[str, str]
) -> None:
    ctx = workspace_project_and_api_key
    with TestClient(app) as client:
        other = client.post(
            "/api/v1/auth/register",
            json={**_REGISTRATION, "email": "other@example.com"},
        ).json()
        other_headers = {"Authorization": f"Bearer {other['access_token']}"}
        other_key = client.post(
            f"/api/v1/workspaces/{other['workspace_id']}/api-keys",
            json={"label": "Other"},
            headers=other_headers,
        ).json()["api_key"]

        payload = {
            "scan_metadata": {
                "scanner_name": "nuclei",
                "scanner_version": "v3",
                "scan_duration_seconds": 1,
            },
            "findings": [_one_finding()],
        }
        response = client.post(
            _batch_url(ctx), json=payload, headers={"X-VulnFlow-API-Key": other_key}
        )

    assert response.status_code == 401


def test_ingest_auto_reopens_remediated_and_quarantined_unselected(
    db_session: Session, workspace_project_and_api_key: dict[str, str]
) -> None:
    ctx = workspace_project_and_api_key
    payload = {
        "scan_metadata": {
            "scanner_name": "nuclei",
            "scanner_version": "v3",
            "scan_duration_seconds": 1,
        },
        "findings": [
            _one_finding(),
            _one_finding(cwe_id="CWE-79", target_host="evil.outside.com"),
        ],
    }

    with TestClient(app) as client:
        first = client.post(
            _batch_url(ctx), json=payload, headers={"X-VulnFlow-API-Key": ctx["api_key"]}
        )
        assert first.status_code == 201
        in_scope = (
            db_session.query(Finding)
            .filter_by(project_id=uuid.UUID(ctx["project_id"]), cwe_id="CWE-89")
            .one()
        )
        out_scope = (
            db_session.query(Finding)
            .filter_by(project_id=uuid.UUID(ctx["project_id"]), cwe_id="CWE-79")
            .one()
        )
        assert in_scope.is_curated_for_report is True
        assert out_scope.is_quarantined is True
        assert out_scope.is_curated_for_report is False

        in_scope.status = "REMEDIATED"
        in_scope.is_curated_for_report = False
        db_session.commit()

        second = client.post(
            _batch_url(ctx), json=payload, headers={"X-VulnFlow-API-Key": ctx["api_key"]}
        )
        assert second.status_code == 201
        assert second.json()["reopened_findings_count"] == 1
        db_session.refresh(in_scope)
        assert in_scope.status == "REOPENED"
        assert in_scope.is_curated_for_report is True


def test_ingest_blocks_expired_roe_and_archived_project(
    db_session: Session, workspace_project_and_api_key: dict[str, str]
) -> None:
    from app.models.audit_log import AuditLog
    from app.models.project import Project

    ctx = workspace_project_and_api_key
    project = db_session.get(Project, uuid.UUID(ctx["project_id"]))
    assert project is not None
    project.roe_start_date = datetime.now(UTC) - timedelta(days=20)
    project.roe_end_date = datetime.now(UTC) - timedelta(days=5)
    db_session.commit()

    payload = {
        "scan_metadata": {
            "scanner_name": "nuclei",
            "scanner_version": "v3",
            "scan_duration_seconds": 1,
        },
        "findings": [_one_finding()],
    }
    with TestClient(app) as client:
        blocked = client.post(
            _batch_url(ctx), json=payload, headers={"X-VulnFlow-API-Key": ctx["api_key"]}
        )
        assert blocked.status_code == 403
        assert (
            db_session.query(AuditLog)
            .filter_by(action="INGEST_BLOCKED_ROE_EXPIRED", target_entity=f"project:{project.id}")
            .count()
            == 1
        )

        project.roe_end_date = datetime.now(UTC) + timedelta(days=5)
        project.status = "ARCHIVED"
        db_session.commit()
        archived = client.post(
            _batch_url(ctx), json=payload, headers={"X-VulnFlow-API-Key": ctx["api_key"]}
        )
        assert archived.status_code == 403

        # Restore active + test manual duplicate returns 409
        project.status = "ACTIVE"
        db_session.commit()
        manual_url = (
            f"/api/v1/workspaces/{ctx['workspace_id']}/projects/{ctx['project_id']}/findings/manual"
        )
        manual_payload = {
            "title": "Manual Finding",
            "severity": "HIGH",
            "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N",
            "cwe_id": "CWE-200",
            "target_host": "rogue.outside.com",
            "proof_of_concept": {"raw_evidence": "proof"},
        }
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": _REGISTRATION["email"], "password": _REGISTRATION["password"]},
        )
        headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}
        m1 = client.post(manual_url, json=manual_payload, headers=headers)
        assert m1.status_code == 201
        assert m1.json()["is_quarantined"] is True
        m2 = client.post(manual_url, json=manual_payload, headers=headers)
        assert m2.status_code == 409
