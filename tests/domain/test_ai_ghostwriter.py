"""PLAN.md FASE 4.6 — AIGhostwriterService orchestration (UC-11; EC-13/EC-14)."""

from typing import Any

import pytest
from app.domain.ai_ghostwriter import LLMTransientError, generate_ai_narrative

from vulnflow_contracts import NarrativeContent, RemediationItem


class _FakeFinding:
    def __init__(self, title: str, cwe_id: str, cvss_score: float, severity: str) -> None:
        self.title = title
        self.cwe_id = cwe_id
        self.cvss_score = cvss_score
        self.severity = severity
        # Sensitive fields that must NEVER reach the adapter (Zero-PoC-to-AI).
        self.target_host = "internal-db.klien.local"
        self.target_port = 5432


class _RecordingAdapter:
    def __init__(self) -> None:
        self.received_findings: list[dict[str, Any]] | None = None

    def generate_narrative(
        self, *, abstract_findings: list[dict[str, Any]], tone: str, language: str
    ) -> tuple[NarrativeContent, int]:
        self.received_findings = abstract_findings
        content = NarrativeContent(
            executive_summary="Ringkasan.",
            business_impact="Dampak.",
            remediations=[
                RemediationItem(cwe_id="CWE-89", vuln_title="SQLi", remediation_guidance="Fix it.")
            ],
        )
        return content, 123


class _AlwaysTransientAdapter:
    def __init__(self) -> None:
        self.call_count = 0

    def generate_narrative(
        self, *, abstract_findings: list[dict[str, Any]], tone: str, language: str
    ) -> tuple[NarrativeContent, int]:
        self.call_count += 1
        raise LLMTransientError("429 Too Many Requests")


class _FailsTwiceThenSucceedsAdapter:
    def __init__(self) -> None:
        self.call_count = 0

    def generate_narrative(
        self, *, abstract_findings: list[dict[str, Any]], tone: str, language: str
    ) -> tuple[NarrativeContent, int]:
        self.call_count += 1
        if self.call_count < 3:
            raise LLMTransientError("timeout")
        content = NarrativeContent(executive_summary="OK", business_impact="OK", remediations=[])
        return content, 50


def test_generate_ai_narrative_only_sends_whitelisted_metadata_to_adapter() -> None:
    adapter = _RecordingAdapter()
    finding = _FakeFinding("SQL Injection", "CWE-89", 9.8, "CRITICAL")

    generate_ai_narrative([finding], tone="formal_executive", language="id", llm_adapter=adapter)

    assert adapter.received_findings == [
        {"title": "SQL Injection", "cwe_id": "CWE-89", "cvss_score": 9.8, "severity": "CRITICAL"}
    ]


def test_generate_ai_narrative_returns_adapter_result_on_success() -> None:
    adapter = _RecordingAdapter()
    finding = _FakeFinding("SQL Injection", "CWE-89", 9.8, "CRITICAL")

    content, tokens, is_fallback = generate_ai_narrative(
        [finding], tone="formal_executive", language="id", llm_adapter=adapter
    )

    assert tokens == 123
    assert is_fallback is False
    assert content.executive_summary == "Ringkasan."


def test_generate_ai_narrative_retries_before_succeeding() -> None:
    adapter = _FailsTwiceThenSucceedsAdapter()
    finding = _FakeFinding("X", "CWE-89", 5.0, "MEDIUM")

    content, tokens, is_fallback = generate_ai_narrative(
        [finding],
        tone="formal_executive",
        language="id",
        llm_adapter=adapter,
        retry_delay_seconds=0,
    )

    assert adapter.call_count == 3
    assert is_fallback is False
    assert tokens == 50


def test_generate_ai_narrative_falls_back_after_exhausting_retries() -> None:
    # EC-14: LLM quota/timeout -> Deterministic Fallback Engine, never an error.
    adapter = _AlwaysTransientAdapter()
    finding = _FakeFinding("SQL Injection", "CWE-89", 9.8, "CRITICAL")

    content, tokens, is_fallback = generate_ai_narrative(
        [finding],
        tone="formal_executive",
        language="id",
        llm_adapter=adapter,
        retry_delay_seconds=0,
    )

    assert adapter.call_count == 3  # exactly 3 attempts, then give up
    assert is_fallback is True
    assert tokens == 0
    assert content.executive_summary
    assert content.remediations[0].cwe_id == "CWE-89"


def test_generate_ai_narrative_fallback_uses_unknown_catalog_entry_for_unmapped_cwe() -> None:
    adapter = _AlwaysTransientAdapter()
    finding = _FakeFinding("Mystery bug", "CWE-99999-NOPE", 1.0, "LOW")

    content, _, is_fallback = generate_ai_narrative(
        [finding],
        tone="formal_executive",
        language="id",
        llm_adapter=adapter,
        retry_delay_seconds=0,
    )

    assert is_fallback is True
    assert content.remediations[0].cwe_id == "CWE-99999-NOPE"
    assert content.remediations[0].vuln_title  # non-empty, from the UNKNOWN catalog entry


def test_generate_ai_narrative_rejects_empty_finding_list() -> None:
    with pytest.raises(ValueError, match="at least one finding"):
        generate_ai_narrative(
            [], tone="formal_executive", language="id", llm_adapter=_RecordingAdapter()
        )


def test_generate_ai_narrative_sanitizes_finding_titles_before_sending_to_adapter() -> None:
    # F4-HIGH-14: sanitize_text strips concrete IPs/ports/hostnames from finding titles
    adapter = _RecordingAdapter()
    finding = _FakeFinding("SQLi found on 192.168.1.100:8080/admin", "CWE-89", 9.8, "CRITICAL")

    generate_ai_narrative([finding], tone="formal_executive", language="id", llm_adapter=adapter)

    assert adapter.received_findings is not None
    title = adapter.received_findings[0]["title"]
    assert "192.168.1.100" not in title
    assert ":8080" not in title
