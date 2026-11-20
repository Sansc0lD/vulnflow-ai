"""PLAN.md FASE 4.6 — AIRouter (SDD §2.6.1.3, UC-11; EC-14 fallback)."""

import os
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from app.domain.ai_ghostwriter import LLMTransientError
from app.main import app
from app.models.ai_narrative import AINarrative
from app.routers.ai import get_llm_adapter
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from vulnflow_contracts import NarrativeContent, RemediationItem

_REGISTRATION = {
    "email": "ai@example.com",
    "password": "Str0ng!Passw0rd",
    "full_name": "AI Tester",
    "workspace_name": "Agensi AI",
}

_PROJECT = {
    "name": "Audit",
    "client_name": "Klien",
    "target_scope": ["*.klien.com"],
    "roe_start_date": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
    "roe_end_date": (datetime.now(UTC) + timedelta(days=30)).isoformat(),
}

_MANUAL_FINDING = {
    "title": "SQL Injection",
    "severity": "CRITICAL",
    "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
    "cwe_id": "CWE-89",
    "target_host": "app.klien.com",
    "proof_of_concept": {"raw_evidence": "' OR 1=1--"},
}


class _FakeAdapter:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.received: list[dict[str, Any]] | None = None

    def generate_narrative(
        self, *, abstract_findings: list[dict[str, Any]], tone: str, language: str
    ) -> tuple[NarrativeContent, int]:
        self.received = abstract_findings
        if self.fail:
            raise LLMTransientError("simulated failure")
        return (
            NarrativeContent(
                executive_summary="Ringkasan.",
                business_impact="Dampak.",
                remediations=[
                    RemediationItem(
                        cwe_id="CWE-89", vuln_title="SQLi", remediation_guidance="Use params."
                    )
                ],
            ),
            321,
        )


@pytest.fixture
def ctx(db_session: object) -> dict[str, str]:
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


def _url(ctx: dict[str, str]) -> str:
    return (
        f"/api/v1/workspaces/{ctx['workspace_id']}/projects/{ctx['project_id']}"
        "/reports/ai-narratives"
    )


def _auth(ctx: dict[str, str]) -> dict[str, str]:
    return {"Authorization": f"Bearer {ctx['token']}"}


def _request_body(ctx: dict[str, str]) -> dict[str, object]:
    return {
        "language": "id",
        "sections_requested": ["executive_summary", "business_impact"],
        "finding_ids": [ctx["finding_id"]],
    }


@pytest.fixture(autouse=True)
def _cleanup_override() -> None:
    yield
    app.dependency_overrides.pop(get_llm_adapter, None)


def test_generate_ai_narrative_succeeds(ctx: dict[str, str]) -> None:
    adapter = _FakeAdapter()
    app.dependency_overrides[get_llm_adapter] = lambda: adapter

    with TestClient(app) as client:
        response = client.post(_url(ctx), json=_request_body(ctx), headers=_auth(ctx))

    assert response.status_code == 200
    body = response.json()
    assert body["is_fallback"] is False
    assert body["tokens_consumed"] == 321
    assert body["narratives"]["executive_summary"] == "Ringkasan."
    # Zero-PoC-to-AI: the adapter must never receive raw PoC/target data.
    assert adapter.received == [
        {"title": "SQL Injection", "cwe_id": "CWE-89", "cvss_score": 9.8, "severity": "CRITICAL"}
    ]


def test_generate_ai_narrative_falls_back_on_llm_failure(ctx: dict[str, str]) -> None:
    app.dependency_overrides[get_llm_adapter] = lambda: _FakeAdapter(fail=True)

    with TestClient(app) as client:
        response = client.post(_url(ctx), json=_request_body(ctx), headers=_auth(ctx))

    assert response.status_code == 200
    body = response.json()
    assert body["is_fallback"] is True
    assert body["tokens_consumed"] == 0
    assert body["narratives"]["remediations"][0]["cwe_id"] == "CWE-89"


def test_generate_ai_narrative_persists_ai_narrative_row(
    db_session: object, ctx: dict[str, str]
) -> None:
    app.dependency_overrides[get_llm_adapter] = lambda: _FakeAdapter()

    with TestClient(app) as client:
        client.post(_url(ctx), json=_request_body(ctx), headers=_auth(ctx))

    narrative = db_session.query(AINarrative).one()
    assert narrative.is_fallback is False
    assert narrative.tokens_consumed == 321


def test_generate_ai_narrative_rejects_finding_from_another_project(ctx: dict[str, str]) -> None:
    app.dependency_overrides[get_llm_adapter] = lambda: _FakeAdapter()
    body = _request_body(ctx)
    body["finding_ids"] = ["00000000-0000-0000-0000-000000000000"]

    with TestClient(app) as client:
        response = client.post(_url(ctx), json=body, headers=_auth(ctx))

    assert response.status_code == 404


def test_generate_ai_narrative_rejects_viewer_role(ctx: dict[str, str]) -> None:
    app.dependency_overrides[get_llm_adapter] = lambda: _FakeAdapter()

    with TestClient(app) as client:
        invite = client.post(
            f"/api/v1/workspaces/{ctx['workspace_id']}/members",
            json={"email": "ai-viewer@example.com", "role": "VIEWER"},
            headers=_auth(ctx),
        ).json()["invitation_token"]
        viewer_token = client.post(
            "/api/v1/auth/register",
            json={
                "email": "ai-viewer@example.com",
                "password": "Str0ng!Passw0rd",
                "full_name": "Viewer",
                "workspace_name": "Unused",
                "invitation_token": invite,
            },
        ).json()["access_token"]

        response = client.post(
            _url(ctx),
            json=_request_body(ctx),
            headers={"Authorization": f"Bearer {viewer_token}"},
        )

    assert response.status_code == 403


def test_generate_ai_narrative_rejects_cross_tenant_project_id(ctx: dict[str, str]) -> None:
    # F4-CRIT-02: Cross-tenant project_id validation in AI
    app.dependency_overrides[get_llm_adapter] = lambda: _FakeAdapter()
    fake_project_id = str(uuid.uuid4())
    url = f"/api/v1/workspaces/{ctx['workspace_id']}/projects/{fake_project_id}/narrative"
    with TestClient(app) as client:
        response = client.post(url, json=_request_body(ctx), headers=_auth(ctx))
    assert response.status_code == 404
    assert response.json()["code"] == "RESOURCE_NOT_FOUND"


def test_generate_ai_narrative_rejects_malformed_uuid_in_finding_ids(ctx: dict[str, str]) -> None:
    # F4-MED-16: Invalid UUID in finding_ids returns 422
    app.dependency_overrides[get_llm_adapter] = lambda: _FakeAdapter()
    body = _request_body(ctx)
    body["finding_ids"] = ["not-a-valid-uuid"]
    with TestClient(app) as client:
        response = client.post(_url(ctx), json=body, headers=_auth(ctx))
    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_FAILED"


def test_ai_narrative_dedups_blocks_quarantined_circuit_breaker_list_and_edit(
    db_session: Session, ctx: dict[str, str]
) -> None:
    from app.core.redis_client import get_optional_redis_client
    from app.models.finding import Finding

    class _LowCeilingRedis:
        def get(self, key: str) -> str | None:
            return "0.000001" if key == "admin:ai:spend_ceiling_usd" else None

    app.dependency_overrides[get_llm_adapter] = lambda: _FakeAdapter()
    try:
        with TestClient(app) as client:
            # Duplicate finding_ids deduped cleanly
            dup_body = _request_body(ctx)
            dup_body["finding_ids"] = [ctx["finding_id"], ctx["finding_id"]]
            r_ok = client.post(_url(ctx), json=dup_body, headers=_auth(ctx))
            assert r_ok.status_code == 200
            narrative_id = r_ok.json()["id"]
            assert narrative_id is not None

            # Out-of-scope / quarantined finding rejected 422
            q_id = client.post(
                f"/api/v1/workspaces/{ctx['workspace_id']}/projects/{ctx['project_id']}/findings/manual",
                json={**_MANUAL_FINDING, "title": "OOS", "target_host": "other.example.org"},
                headers=_auth(ctx),
            ).json()["id"]
            q_body = _request_body(ctx)
            q_body["finding_ids"] = [q_id]
            assert client.post(_url(ctx), json=q_body, headers=_auth(ctx)).status_code == 422

            # Circuit breaker active triggers deterministic fallback without calling LLM
            app.dependency_overrides[get_optional_redis_client] = lambda: _LowCeilingRedis()
            fb = client.post(_url(ctx), json=_request_body(ctx), headers=_auth(ctx))
            assert fb.status_code == 200
            assert fb.json()["is_fallback"] is True

            # List & edit narrative with HTML sanitization + approval status
            listed = client.get(_url(ctx), headers=_auth(ctx))
            assert listed.status_code == 200
            assert len(listed.json()) == 2

            updated = client.put(
                f"{_url(ctx)}/{narrative_id}",
                json={
                    "executive_summary": "<script>alert(1)</script>Clean summary",
                    "business_impact": '<p onclick="evil()">Low</p>',
                    "remediations": [
                        {
                            "cwe_id": "CWE-89",
                            "vuln_title": "SQLi <iframe src='x'></iframe>",
                            "remediation_guidance": 'Use <a href="javascript:x()">params</a>.',
                        }
                    ],
                    "approval_status": "APPROVED",
                },
                headers=_auth(ctx),
            )
            assert updated.status_code == 200
            up_data = updated.json()
            assert up_data["approval_status"] == "APPROVED"
            assert "<script>" not in up_data["narratives"]["executive_summary"]
            assert "onclick" not in up_data["narratives"]["business_impact"]
            assert "<iframe" not in up_data["narratives"]["remediations"][0]["vuln_title"]

            # Clean up reference check
            assert db_session.query(Finding).filter_by(id=uuid.UUID(ctx["finding_id"])).count() == 1
    finally:
        app.dependency_overrides.pop(get_optional_redis_client, None)
        app.dependency_overrides.pop(get_llm_adapter, None)
