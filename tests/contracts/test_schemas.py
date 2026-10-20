"""Unit tests — PLAN.md FASE 1.7: serialisasi/deserialisasi kontrak Pydantic V2.

Setiap round-trip test memakai contoh JSON PERSIS dari SDD §2.6.1/§2.6.3,
dan setiap test validasi memastikan input yang melanggar aturan SDD ditolak.
"""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from vulnflow_contracts import (
    AINarrativeRequest,
    AINarrativeResponse,
    BatchIngestRequest,
    ErrorCode,
    ManualFindingRequest,
    MidtransCheckoutResponse,
    MidtransWebhookPayload,
    ProofOfConceptSchema,
    RegisterRequest,
    ReportJobStatusResponse,
    StandardErrorEnvelope,
    TokenResponse,
    UnifiedVulnerabilityFinding,
)

# --- error_envelope -----------------------------------------------------


def test_standard_error_envelope_round_trip() -> None:
    envelope = StandardErrorEnvelope(
        code=ErrorCode.VALIDATION_FAILED,
        message="Payload tidak valid.",
        details={"field": "cwe_id", "issue": "pattern tidak cocok"},
        timestamp=datetime.now(UTC),
    )
    dumped = envelope.model_dump(mode="json")
    assert dumped["status"] == "error"
    assert dumped["code"] == "VALIDATION_FAILED"
    assert StandardErrorEnvelope.model_validate(dumped) == envelope


# --- finding_schemas ------------------------------------------------------


def test_unified_vulnerability_finding_accepts_sdd_example() -> None:
    finding = UnifiedVulnerabilityFinding.model_validate(
        {
            "title": "Git Config File Disclosure",
            "severity": "MEDIUM",
            "cvss_version": "3.1",
            "cvss_score": 5.3,
            "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N",
            "cwe_id": "CWE-538",
            "target_host": "staging.clientdomain.com",
            "target_port": 443,
            "protocol": "https",
            "source_tool": "nuclei",
            "proof_of_concept": {
                "raw_evidence": "HTTP/1.1 200 OK\n[core]\nrepositoryformatversion = 0"
            },
        }
    )
    assert finding.cwe_id == "CWE-538"
    assert finding.target_port == 443


def test_unified_vulnerability_finding_defaults_cwe_to_unknown() -> None:
    finding = UnifiedVulnerabilityFinding(
        title="Unscoped finding",
        severity="INFO",
        target_host="10.0.0.5",
        source_tool="nmap",
        proof_of_concept=ProofOfConceptSchema(raw_evidence="banner grab"),
    )
    assert finding.cwe_id == "UNKNOWN"
    assert finding.target_port is None  # EC-09: non-network finding, no port


@pytest.mark.parametrize("bad_cwe", ["CWE-", "89", "cwe-89", "CWE-89x"])
def test_unified_vulnerability_finding_rejects_malformed_cwe(bad_cwe: str) -> None:
    with pytest.raises(ValidationError):
        UnifiedVulnerabilityFinding(
            title="x",
            severity="LOW",
            cwe_id=bad_cwe,
            target_host="10.0.0.5",
            source_tool="nmap",
            proof_of_concept=ProofOfConceptSchema(raw_evidence="x"),
        )


@pytest.mark.parametrize("bad_port", [0, 65536, -1])
def test_unified_vulnerability_finding_rejects_out_of_range_port(bad_port: int) -> None:
    with pytest.raises(ValidationError):
        UnifiedVulnerabilityFinding(
            title="x",
            severity="LOW",
            target_host="10.0.0.5",
            target_port=bad_port,
            source_tool="nmap",
            proof_of_concept=ProofOfConceptSchema(raw_evidence="x"),
        )


def test_unified_vulnerability_finding_endpoint_path_defaults_empty_and_differentiates_dedup() -> (
    None
):
    """EC-08: dua temuan di host+port sama tapi endpoint_path berbeda bukan duplikat."""
    common = {
        "title": "SQL Injection",
        "severity": "HIGH",
        "cwe_id": "CWE-89",
        "target_host": "api.targetapp.com",
        "target_port": 443,
        "source_tool": "nuclei",
        "proof_of_concept": {"raw_evidence": "x"},
    }
    finding_a = UnifiedVulnerabilityFinding(**common, endpoint_path="/search.php")
    finding_b = UnifiedVulnerabilityFinding(**common, endpoint_path="/login.php")
    assert finding_a.endpoint_path != finding_b.endpoint_path

    finding_default = UnifiedVulnerabilityFinding(**common)
    assert finding_default.endpoint_path == ""


def test_batch_ingest_request_requires_at_least_one_finding() -> None:
    with pytest.raises(ValidationError):
        BatchIngestRequest(
            scan_metadata={
                "scanner_name": "nuclei",
                "scanner_version": "v3.2.4",
                "scan_duration_seconds": 142,
            },
            findings=[],
        )


def test_manual_finding_request_accepts_sdd_example() -> None:
    request = ManualFindingRequest.model_validate(
        {
            "title": "Broken Object Level Authorization on User Profile Endpoint",
            "severity": "HIGH",
            "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:N",
            "cwe_id": "CWE-639",
            "target_host": "api.targetapp.com",
            "target_port": 443,
            "protocol": "https",
            "proof_of_concept": {
                "raw_evidence": "GET /api/v1/users/9981 HTTP/1.1",
                "reproduction_steps": ["Login sebagai User A", "GET /api/v1/users/9981"],
            },
        }
    )
    assert request.cwe_id == "CWE-639"
    assert len(request.proof_of_concept.reproduction_steps) == 2


# --- auth_schemas -----------------------------------------------------


def test_register_request_accepts_strong_password() -> None:
    request = RegisterRequest(
        email="auditor@agency.corp",
        password="SecurePassword123!",
        full_name="Ahmad Dani",
        workspace_name="Agency Security Corp",
    )
    assert request.email == "auditor@agency.corp"


@pytest.mark.parametrize(
    "weak_password",
    [
        "short1!",  # < 8 karakter
        "alllowercase123!",  # tanpa huruf besar
        "ALLUPPERCASE123!",  # tanpa huruf kecil
        "NoDigitsHere!",  # tanpa angka
        "NoSymbolsHere123",  # tanpa karakter khusus
    ],
)
def test_register_request_rejects_weak_password(weak_password: str) -> None:
    with pytest.raises(ValidationError):
        RegisterRequest(
            email="auditor@agency.corp",
            password=weak_password,
            full_name="Ahmad Dani",
            workspace_name="Agency Security Corp",
        )


def test_token_response_round_trip() -> None:
    token = TokenResponse.model_validate(
        {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "bearer",
            "expires_in": 86400,
            "user": {
                "id": "usr_uuid_7712",
                "email": "auditor@agency.corp",
                "full_name": "Ahmad Dani",
            },
            "workspaces": [
                {"id": "wsp_uuid_9921", "name": "Agency Security Corp", "role": "MANAGER"}
            ],
        }
    )
    assert token.workspaces[0].role == "MANAGER"


def test_register_request_accepts_invitation_token() -> None:
    request = RegisterRequest(
        email="pentester@agency.corp",
        password="SecurePassword123!",
        full_name="Budi",
        workspace_name="Agency Security Corp",
        invitation_token="inv_tok_abc123",
    )
    assert request.invitation_token == "inv_tok_abc123"


def test_register_request_rejects_null_byte_in_password() -> None:
    with pytest.raises(ValidationError):
        RegisterRequest(
            email="auditor@agency.corp",
            password="Secure\x00Password123!",
            full_name="Ahmad Dani",
            workspace_name="Agency Security Corp",
        )


def test_register_request_rejects_password_over_128_chars() -> None:
    with pytest.raises(ValidationError):
        RegisterRequest(
            email="auditor@agency.corp",
            password="Aa1!" * 33,  # 132 karakter
            full_name="Ahmad Dani",
            workspace_name="Agency Security Corp",
        )


# --- ai_schemas -----------------------------------------------------


def test_ai_narrative_request_and_response_round_trip() -> None:
    request = AINarrativeRequest(
        tone="formal_executive",
        language="id",
        sections_requested=["executive_summary", "business_impact", "remediation_roadmap"],
        finding_ids=["fnd_uuid_001", "fnd_uuid_002", "fnd_uuid_003"],
    )
    assert request.language == "id"

    response = AINarrativeResponse.model_validate(
        {
            "narratives": {
                "executive_summary": "Berdasarkan audit keamanan...",
                "business_impact": "Eksploitasi kerentanan...",
                "remediations": [
                    {
                        "cwe_id": "CWE-89",
                        "vuln_title": "SQL Injection",
                        "remediation_guidance": "Gunakan prepared statement...",
                    }
                ],
            },
            "tokens_consumed": 1420,
            "generated_at": "2026-09-23T18:15:00Z",
        }
    )
    assert response.tokens_consumed == 1420
    assert response.narratives.remediations[0].cwe_id == "CWE-89"
    assert response.is_fallback is False  # default — UC-11b hanya true saat fallback aktif


# --- report_schemas -----------------------------------------------------


def test_report_job_status_response_handles_completed_shape() -> None:
    status = ReportJobStatusResponse.model_validate(
        {
            "job_id": "job_pdf_883192",
            "status": "COMPLETED",
            "progress_percentage": 100,
            "report_id": "rep_uuid_1029",
            "download_url": "https://storage.vulnflow.ai/reports/rep_uuid_1029.pdf?X-Amz-Signature=...",
            "expires_in_seconds": 900,
        }
    )
    assert status.report_id == "rep_uuid_1029"


def test_report_job_status_response_handles_failed_shape() -> None:
    status = ReportJobStatusResponse.model_validate(
        {
            "job_id": "job_pdf_883192",
            "status": "FAILED",
            "error_message": "Gagal merender CSS Paged Media WeasyPrint akibat timeout.",
        }
    )
    assert status.report_id is None
    assert status.error_message is not None


# --- billing_schemas -----------------------------------------------------


def test_midtrans_checkout_response_round_trip() -> None:
    response = MidtransCheckoutResponse.model_validate(
        {
            "order_id": "ORD-WSP01-1727452800",
            "gross_amount": 750000,
            "snap_token": "7a9f8b2c-4e1d-3a5b-8c7e-9f0a1b2c3d4e",
            "redirect_url": "https://app.sandbox.midtrans.com/snap/v2/vtweb/7a9f8b2c",
        }
    )
    assert response.gross_amount == 750000


def test_midtrans_webhook_payload_accepts_sdd_example() -> None:
    payload = MidtransWebhookPayload.model_validate(
        {
            "order_id": "ORD-WSP01-1727452800",
            "status_code": "200",
            "gross_amount": "750000.00",
            "signature_key": "9a8b7c6d" * 16,  # 128 hex chars
            "transaction_status": "settlement",
            "payment_type": "qris",
            "transaction_time": "2026-09-27 23:45:00",
        }
    )
    assert payload.transaction_status == "settlement"


@pytest.mark.parametrize("bad_amount", ["750000", "750000.0", "750000.000", "abc.00"])
def test_midtrans_webhook_payload_rejects_unnormalized_gross_amount(bad_amount: str) -> None:
    with pytest.raises(ValidationError):
        MidtransWebhookPayload(
            order_id="ORD-1",
            status_code="200",
            gross_amount=bad_amount,
            signature_key="9a8b7c6d" * 16,
            transaction_status="settlement",
            payment_type="qris",
            transaction_time="2026-09-27 23:45:00",
        )


def test_midtrans_webhook_payload_accepts_uppercase_hex_signature() -> None:
    payload = MidtransWebhookPayload(
        order_id="ORD-1",
        status_code="200",
        gross_amount="750000.00",
        signature_key=("9A8B7C6D" * 16),
        transaction_status="settlement",
        payment_type="qris",
        transaction_time="2026-09-27 23:45:00",
    )
    assert payload.signature_key.isupper()


def test_midtrans_webhook_payload_ignores_unknown_fields_from_real_midtrans() -> None:
    """Payload Midtrans asli/sandbox selalu menyertakan field tambahan di luar
    7 field contoh SDD (transaction_id, fraud_status, currency, dll.)."""
    payload = MidtransWebhookPayload.model_validate(
        {
            "order_id": "ORD-1",
            "status_code": "200",
            "gross_amount": "750000.00",
            "signature_key": "9a8b7c6d" * 16,
            "transaction_status": "settlement",
            "payment_type": "qris",
            "transaction_time": "2026-09-27 23:45:00",
            "transaction_id": "extra-field-from-real-midtrans",
            "fraud_status": "accept",
            "currency": "IDR",
        }
    )
    assert payload.order_id == "ORD-1"


def test_midtrans_webhook_payload_rejects_malformed_signature() -> None:
    with pytest.raises(ValidationError):
        MidtransWebhookPayload(
            order_id="ORD-1",
            status_code="200",
            gross_amount="750000.00",
            signature_key="not-a-valid-sha512-hex-digest",
            transaction_status="settlement",
            payment_type="qris",
            transaction_time="2026-09-27 23:45:00",
        )
