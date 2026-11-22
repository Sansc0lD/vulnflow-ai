"""Integration tests for Waves 2 & 3 (#5, #7, #8, #9, #10)."""

import base64
import io
import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import httpx
import pytest
from app.core.redis_client import get_optional_redis_client
from app.core.seeder import get_seed_admin_password, get_seed_admin_totp_secret, seed_defaults
from app.core.totp import compute_totp
from app.domain.fallback import get_fallback_narrative
from app.domain.sanitizer import whitelist_tech_stack
from app.main import app
from app.models.finding import Finding
from app.models.project import Project
from app.models.proof_of_concept import ProofOfConcept
from app.models.subscription import Subscription
from app.models.workspace import Workspace
from app.routers.ai import get_ai_enqueuer
from app.services.email_service import get_email_sender
from app.services.ollama_adapter import OllamaLLMAdapter
from app.services.report_renderer import build_report_html
from app.workers.report_worker import compile_report
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy.orm import Session


class _MemoryRedis:
    def __init__(self) -> None:
        self._store: dict[str, str] = {}
        self._counters: dict[str, int] = {}

    def get(self, key: str) -> str | None:
        return self._store.get(key)

    def set(self, key: str, value: str, *, ex: int | None = None) -> bool:
        self._store[key] = value
        return True

    def incr(self, key: str) -> int:
        self._counters[key] = self._counters.get(key, 0) + 1
        return self._counters[key]

    def expire(self, key: str, ttl: int) -> bool:
        return True


class _FakeEmailSender:
    def __init__(self) -> None:
        self.sent: list[dict[str, str]] = []

    def send_email(self, *, to_email: str, subject: str, html_body: str, text_body: str) -> bool:
        self.sent.append({"to": to_email, "subject": subject, "text": text_body})
        return True


class _FakeS3Storage:
    def __init__(self) -> None:
        self.objects: dict[str, tuple[bytes, str]] = {}

    def upload_bytes(self, key: str, data: bytes, *, content_type: str = "application/pdf") -> None:
        self.objects[key] = (data, content_type)

    def download_bytes(self, key: str) -> tuple[bytes, str] | None:
        return self.objects.get(key)


def _register_user(client: TestClient, email: str = "ent@example.com") -> dict[str, str]:
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "Str0ng!Passw0rd",
            "full_name": "Enterprise Requester",
            "workspace_name": f"WS-{email}",
        },
    )
    assert resp.status_code == 201
    return resp.json()


def test_enterprise_inquiry_and_admin_unlimited_provisioning(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SEED_ADMIN_PASSWORD", "SeedAdmin!2026")
    monkeypatch.setenv("SEED_ADMIN_TOTP_SECRET", "JBSWY3DPEHPK3PXP")
    seed_defaults(db_session)

    fake_redis = _MemoryRedis()
    fake_email = _FakeEmailSender()
    app.dependency_overrides[get_optional_redis_client] = lambda: fake_redis
    app.dependency_overrides[get_email_sender] = lambda: fake_email
    try:
        with TestClient(app) as client:
            reg = _register_user(client, "ceo@corp.example")
            ws_id = reg["workspace_id"]
            user_headers = {"Authorization": f"Bearer {reg['access_token']}"}

            # Public inquiry
            pub_inq = client.post(
                "/api/v1/public/enterprise-inquiries",
                json={
                    "company_name": "Nusantara Cyber",
                    "contact_name": "Rina",
                    "contact_email": "rina@nusantara.io",
                    "team_size": "21-50",
                    "estimated_monthly_reports": 150,
                    "requirements": "Dedicated VPC & 2000 findings CLI batch size.",
                },
            )
            assert pub_inq.status_code == 201
            assert pub_inq.json()["status"] == "NEW"

            # Workspace-linked inquiry
            ws_inq = client.post(
                f"/api/v1/workspaces/{ws_id}/billing/enterprise-inquiry",
                headers=user_headers,
                json={
                    "company_name": "Corp Sec",
                    "contact_name": "Budi",
                    "contact_email": "budi@corp.example",
                    "team_size": "50+",
                    "requirements": "Unlimited PDF exports and custom SLA.",
                },
            )
            assert ws_inq.status_code == 201
            inq_id = ws_inq.json()["id"]
            assert ws_inq.json()["workspace_id"] == ws_id
            assert len(fake_email.sent) == 2

            # Superadmin login
            admin_login = client.post(
                "/api/v1/auth/login",
                json={
                    "email": "admin@vulnflow.local",
                    "password": get_seed_admin_password(),
                    "totp_code": compute_totp(get_seed_admin_totp_secret()),
                },
            ).json()
            admin_headers = {"Authorization": f"Bearer {admin_login['access_token']}"}

            inquiries = client.get(
                "/api/v1/admin/enterprise-inquiries", headers=admin_headers
            ).json()
            assert len(inquiries) == 2

            # Provision ENTERPRISE unlimited (-1 quota) + 2500 CLI batch limit
            override = client.patch(
                f"/api/v1/admin/workspaces/{ws_id}/subscription",
                headers=admin_headers,
                json={
                    "tier": "ENTERPRISE",
                    "monthly_report_quota": -1,
                    "custom_batch_limit": 2500,
                    "reason": "Signed annual Enterprise MSA",
                },
            )
            assert override.status_code == 200
            assert override.json()["is_unlimited"] is True
            assert override.json()["custom_batch_limit"] == 2500

            upd_inq = client.patch(
                f"/api/v1/admin/enterprise-inquiries/{inq_id}",
                headers=admin_headers,
                json={"status": "PROVISIONED", "admin_notes": "Activated."},
            )
            assert upd_inq.status_code == 200
            assert upd_inq.json()["status"] == "PROVISIONED"

            sub_resp = client.get(
                f"/api/v1/workspaces/{ws_id}/billing/subscription",
                headers=user_headers,
            )
            assert sub_resp.status_code == 200
            assert sub_resp.json()["tier"] == "ENTERPRISE"
            assert sub_resp.json()["is_unlimited"] is True
    finally:
        app.dependency_overrides.pop(get_optional_redis_client, None)
        app.dependency_overrides.pop(get_email_sender, None)


def test_ai_async_queue_rate_limit_and_status_polling(db_session: Session) -> None:
    fake_redis = _MemoryRedis()
    queued_calls: list[dict[str, Any]] = []

    def _fake_ai_enqueuer(**kwargs: Any) -> str:
        queued_calls.append(kwargs)
        return "ai-job-001"

    app.dependency_overrides[get_optional_redis_client] = lambda: fake_redis
    app.dependency_overrides[get_ai_enqueuer] = lambda: _fake_ai_enqueuer
    try:
        with TestClient(app) as client:
            reg = _register_user(client, "aiasync@example.com")
            ws_id = reg["workspace_id"]
            headers = {"Authorization": f"Bearer {reg['access_token']}"}
            proj_id = client.post(
                f"/api/v1/workspaces/{ws_id}/projects",
                headers=headers,
                json={
                    "name": "API Pentest",
                    "client_name": "FinTech",
                    "target_scope": ["api.fintech.local"],
                    "roe_start_date": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
                    "roe_end_date": (datetime.now(UTC) + timedelta(days=10)).isoformat(),
                    "tech_stack": {
                        "language": "python",
                        "framework": "fastapi",
                        "database": "postgresql",
                    },
                },
            ).json()["id"]
            finding_id = client.post(
                f"/api/v1/workspaces/{ws_id}/projects/{proj_id}/findings/manual",
                headers=headers,
                json={
                    "title": "SQLi",
                    "severity": "CRITICAL",
                    "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
                    "cwe_id": "CWE-89",
                    "target_host": "api.fintech.local",
                    "proof_of_concept": {"raw_evidence": "' OR 1=1--"},
                },
            ).json()["id"]

            async_url = f"/api/v1/workspaces/{ws_id}/projects/{proj_id}/reports/ai-narratives/async"
            payload = {
                "language": "id",
                "sections_requested": ["executive_summary"],
                "finding_ids": [finding_id],
            }
            for _ in range(3):
                r = client.post(async_url, json=payload, headers=headers)
                assert r.status_code == 202
                assert r.json()["job_id"] == "ai-job-001"

            # 4th call inside same minute triggers 429 RPM guard
            limited = client.post(async_url, json=payload, headers=headers)
            assert limited.status_code == 429
            assert limited.headers.get("retry-after") == "60"

            status_resp = client.get(
                f"/api/v1/workspaces/{ws_id}/projects/{proj_id}/reports/ai-narratives/jobs/ai-job-001",
                headers=headers,
            )
            assert status_resp.status_code == 200
            assert status_resp.json()["status"] == "QUEUED"
    finally:
        app.dependency_overrides.pop(get_optional_redis_client, None)
        app.dependency_overrides.pop(get_ai_enqueuer, None)


def test_modular_report_poc_attachments_and_public_verification(db_session: Session) -> None:
    os_key = "9EL3Yj4ANNfiuFYY7zBoYc6XLnoD3GZpcBc6lWGLL9U="
    del os_key
    ws = Workspace(name="Audit Studio")
    db_session.add(ws)
    db_session.flush()
    sub = Subscription(
        workspace_id=ws.id,
        tier="FREE",
        monthly_report_quota=3,
        quota_reset_date=datetime.now(UTC) + timedelta(days=30),
    )
    proj = Project(
        workspace_id=ws.id,
        name="Portal Audit",
        client_name="Secret Client Corp",
        target_scope="portal.secretclient.local",
        roe_start_date=datetime.now(UTC) - timedelta(days=1),
        roe_end_date=datetime.now(UTC) + timedelta(days=10),
        tech_stack={"language": "python", "framework": "fastapi"},
    )
    db_session.add_all([sub, proj])
    db_session.flush()

    f = Finding(
        project_id=proj.id,
        dedup_hash="h1",
        title="Stored XSS",
        severity="HIGH",
        cvss_score=Decimal("7.5"),
        cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N",
        cwe_id="CWE-79",
        target_host="portal.secretclient.local",
        source_tool="manual",
        is_curated_for_report=True,
    )
    db_session.add(f)
    db_session.flush()

    buf = io.BytesIO()
    Image.new("RGB", (32, 32), (255, 0, 0)).save(buf, format="PNG")
    storage = _FakeS3Storage()
    att_key = f"workspaces/{ws.id}/projects/{proj.id}/findings/{f.id}/poc.png"
    storage.upload_bytes(att_key, buf.getvalue(), content_type="image/png")

    poc = ProofOfConcept(
        finding_id=f.id,
        encrypted_raw_evidence=b"cipher",
        iv_nonce=b"123456789012",
        auth_tag=b"1234567890123456",
        reproduction_steps=["Step 1: Inject payload"],
        attachment_file_urls=[f"https://minio.local/vulnflow-bucket/{att_key}"],
    )
    db_session.add(poc)
    db_session.commit()

    captured_html: dict[str, str] = {}

    def _capture_render(html: str) -> bytes:
        captured_html["html"] = html
        return b"%PDF-fake"

    report = compile_report(
        db_session,
        storage,
        workspace_id=ws.id,
        project_id=proj.id,
        report_title="Portal Security Audit",
        executive_summary="Exec summary.",
        business_impact="Business impact.",
        watermark_text="FREE TIER PREVIEW",
        theme_options={"report_language": "id", "show_toc": True, "show_methodology": True},
        render_fn=_capture_render,
    )

    assert report.verification_code is not None
    assert report.sha256_hash is not None
    assert "Table of Contents" not in captured_html["html"]
    assert "Daftar Isi" in captured_html["html"]
    expected_uri = f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode('ascii')}"
    assert expected_uri in captured_html["html"]
    assert "target-counter(attr(href), page)" in captured_html["html"]

    # Check default English headings preserve exact h2 assertions
    en_html = build_report_html(
        report_title="R",
        client_name="C",
        findings=[{"title": "X", "severity": "HIGH", "cvss_score": 7.5, "cwe_id": "CWE-79"}],
        executive_summary="S",
        business_impact="B",
        watermark_text=None,
    )
    assert "<h2>Executive Summary</h2>" in en_html
    assert "<h2>Findings Summary</h2>" in en_html

    # Public verification must expose provenance without leaking client name or PoC
    with TestClient(app) as client:
        ok = client.get(f"/api/v1/public/verify/{report.verification_code}")
        assert ok.status_code == 200
        body = ok.json()
        assert body["valid"] is True
        assert body["sha256_hash"] == report.sha256_hash
        assert "Secret Client Corp" not in json.dumps(body)

        missing = client.get("/api/v1/public/verify/VF-0000-0000-0000")
        assert missing.status_code == 200
        assert missing.json()["valid"] is False


def test_stack_aware_remediation_whitelist_and_ollama_adapter() -> None:
    sanitized = whitelist_tech_stack(
        {
            "language": "PYTHON",
            "framework": "fastapi",
            "evil_poc": "http://10.0.0.1/admin ' OR 1=1",
        }
    )
    assert sanitized == {"language": "python", "framework": "fastapi"}

    entry = get_fallback_narrative(
        "CWE-89", tech_stack={"language": "python", "framework": "fastapi"}
    )
    assert "FastAPI/SQLAlchemy" in entry["remediation"]

    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = request.content.decode("utf-8")
        return httpx.Response(
            200,
            json={
                "message": {
                    "content": json.dumps(
                        {
                            "executive_summary": "Summary",
                            "business_impact": "Impact",
                            "remediations": [],
                        }
                    )
                },
                "prompt_eval_count": 40,
                "eval_count": 60,
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    adapter = OllamaLLMAdapter(
        base_url="http://127.0.0.1:11434", model="llama3.1:8b", client=client
    )
    narrative, total = adapter.generate_narrative(
        abstract_findings=[
            {
                "title": "SQLi",
                "cwe_id": "CWE-89",
                "cvss_score": 9.8,
                "severity": "CRITICAL",
                "target_host": "secret.internal",
            }
        ],
        tone="formal_executive",
        language="en",
        tech_stack={"language": "python", "framework": "fastapi"},
    )
    assert narrative.executive_summary == "Summary"
    assert total == 100
    assert adapter.last_usage["prompt_tokens"] == 40
    assert adapter.last_usage["candidates_tokens"] == 60
    assert "secret.internal" not in captured["body"]
    assert "framework=fastapi" in captured["body"]
