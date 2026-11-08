"""`vulnflow push` HTTP ingest client — PLAN.md FASE 5.6 (EC-07/EC-10)."""

from pathlib import Path

import httpx
import pytest
from vulnflow.ingest_client import (
    FreeTierBatchLimitError,
    IngestClientError,
    IngestTransientError,
    chunk_findings,
    compute_file_hash,
    compute_idempotency_key,
    push_batch,
)

from vulnflow_contracts import (
    ProofOfConceptSchema,
    Protocol,
    ScanMetadata,
    Severity,
    SourceTool,
    UnifiedVulnerabilityFinding,
)

_SCAN_METADATA = ScanMetadata(
    scanner_name="nuclei", scanner_version="3.0.0", scan_duration_seconds=1.0
)


def _finding(title: str = "Test finding") -> UnifiedVulnerabilityFinding:
    return UnifiedVulnerabilityFinding(
        title=title,
        severity=Severity.HIGH,
        cwe_id="UNKNOWN",
        target_host="target.example.com",
        protocol=Protocol.HTTP,
        source_tool=SourceTool.NUCLEI,
        proof_of_concept=ProofOfConceptSchema(raw_evidence="evidence"),
    )


def test_compute_idempotency_key_without_chunk_index_is_file_hash() -> None:
    assert compute_idempotency_key("abc123") == "abc123"


def test_compute_idempotency_key_with_chunk_index_is_unique_per_chunk() -> None:
    key0 = compute_idempotency_key("abc123", chunk_index=0)
    key1 = compute_idempotency_key("abc123", chunk_index=1)

    assert key0 != key1
    assert key0 == "abc123:0"


def test_compute_idempotency_key_is_stable_across_retries() -> None:
    # Same file, same chunk, re-computed independently (simulating a retry) -> identical key.
    assert compute_idempotency_key("abc123", chunk_index=2) == compute_idempotency_key(
        "abc123", chunk_index=2
    )


def test_compute_file_hash_is_deterministic(tmp_path: Path) -> None:
    file_path = tmp_path / "scan.json"
    file_path.write_text("same content", encoding="utf-8")

    assert compute_file_hash(file_path) == compute_file_hash(file_path)


def test_compute_file_hash_differs_for_different_content(tmp_path: Path) -> None:
    file_a = tmp_path / "a.json"
    file_b = tmp_path / "b.json"
    file_a.write_text("content a", encoding="utf-8")
    file_b.write_text("content b", encoding="utf-8")

    assert compute_file_hash(file_a) != compute_file_hash(file_b)


def test_chunk_findings_splits_into_requested_size() -> None:
    findings = [_finding(f"f{i}") for i in range(7)]

    chunks = chunk_findings(findings, size=3)

    assert [len(c) for c in chunks] == [3, 3, 1]


def test_chunk_findings_single_chunk_when_under_size() -> None:
    findings = [_finding()]

    chunks = chunk_findings(findings, size=500)

    assert len(chunks) == 1


def test_push_batch_succeeds_on_first_attempt() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["x-vulnflow-api-key"] == "vf_live_test"
        assert request.headers["idempotency-key"] == "hash:0"
        return httpx.Response(
            201,
            json={"new_findings_count": 1, "duplicate_findings_count": 0, "quarantined_count": 0},
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))

    response = push_batch(
        client,
        api_url="https://api.vulnflow.ai",
        workspace_id="wsp-01",
        project_id="prj-01",
        api_key="vf_live_test",
        findings=[_finding()],
        scan_metadata=_SCAN_METADATA,
        idempotency_key="hash:0",
    )

    assert response.new_findings_count == 1


def test_push_batch_retries_transient_5xx_then_succeeds() -> None:
    attempts = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        attempts["count"] += 1
        if attempts["count"] < 3:
            return httpx.Response(503, json={"message": "unavailable"})
        return httpx.Response(
            201,
            json={"new_findings_count": 1, "duplicate_findings_count": 0, "quarantined_count": 0},
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))

    response = push_batch(
        client,
        api_url="https://api.vulnflow.ai",
        workspace_id="wsp-01",
        project_id="prj-01",
        api_key="vf_live_test",
        findings=[_finding()],
        scan_metadata=_SCAN_METADATA,
        idempotency_key="hash:0",
        retry_delay_seconds=0.0,
    )

    assert response.new_findings_count == 1
    assert attempts["count"] == 3


def test_push_batch_raises_transient_error_after_exhausting_retries() -> None:
    client = httpx.Client(
        transport=httpx.MockTransport(lambda req: httpx.Response(503, json={"message": "down"}))
    )

    with pytest.raises(IngestTransientError):
        push_batch(
            client,
            api_url="https://api.vulnflow.ai",
            workspace_id="wsp-01",
            project_id="prj-01",
            api_key="vf_live_test",
            findings=[_finding()],
            scan_metadata=_SCAN_METADATA,
            idempotency_key="hash:0",
            retry_delay_seconds=0.0,
        )


def test_push_batch_raises_free_tier_error_on_413() -> None:
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda req: httpx.Response(413, json={"message": "Free tier is limited to 50."})
        )
    )

    with pytest.raises(FreeTierBatchLimitError):
        push_batch(
            client,
            api_url="https://api.vulnflow.ai",
            workspace_id="wsp-01",
            project_id="prj-01",
            api_key="vf_live_test",
            findings=[_finding()],
            scan_metadata=_SCAN_METADATA,
            idempotency_key="hash:0",
        )


def test_push_batch_raises_client_error_on_401_without_retrying() -> None:
    attempts = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        attempts["count"] += 1
        return httpx.Response(401, json={"message": "invalid key"})

    client = httpx.Client(transport=httpx.MockTransport(handler))

    with pytest.raises(IngestClientError):
        push_batch(
            client,
            api_url="https://api.vulnflow.ai",
            workspace_id="wsp-01",
            project_id="prj-01",
            api_key="vf_live_test",
            findings=[_finding()],
            scan_metadata=_SCAN_METADATA,
            idempotency_key="hash:0",
        )

    assert attempts["count"] == 1
