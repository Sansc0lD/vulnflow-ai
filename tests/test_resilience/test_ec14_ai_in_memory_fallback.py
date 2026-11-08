"""PLAN.md FASE 7.2 — EC-14: In-Memory Deterministic Fallback on LLM Exhaustion.

EDGE_CASES_AND_RESILIENCE.md §6 item 14 & SRS UC-11b:
When commercial LLM APIs are unreachable, return HTTP 429 quota exhaustion,
or experience persistent network timeouts, `AIGhostwriterService` must never
block report compilation or leave empty sections. It gracefully transitions
to the in-memory `DeterministicFallbackEngine` (`cwe_catalog.json`) with `is_fallback: True`.
"""

from decimal import Decimal
from typing import Any

from app.domain.ai_ghostwriter import LLMTransientError, generate_ai_narrative
from app.domain.fallback import get_fallback_narrative, load_catalog
from app.models.finding import Finding

from vulnflow_contracts import NarrativeContent


class _FailingLLMAdapter:
    """Simulates an external LLM provider suffering rate limits (429) or timeouts."""

    def generate_narrative(
        self, *, abstract_findings: list[dict[str, Any]], tone: str, language: str
    ) -> tuple[NarrativeContent, int]:
        raise LLMTransientError("HTTP 429: Vertex AI / OpenAI quota exhausted.")


def test_ec14_in_memory_catalog_serves_o1_lookup() -> None:
    """cwe_catalog.json provides O(1) in-memory cached lookup for remediation guidance."""
    catalog = load_catalog()
    assert "CWE-89" in catalog
    assert "UNKNOWN" in catalog

    sqli_fallback = get_fallback_narrative("CWE-89")
    assert "SQL" in sqli_fallback["title"]
    assert sqli_fallback["remediation"]

    # Unknown CWE falls back to UNKNOWN default
    unknown_fallback = get_fallback_narrative("CWE-99999")
    assert unknown_fallback == catalog["UNKNOWN"]


def test_ec14_ghostwriter_triggers_fallback_when_llm_fails() -> None:
    """When adapter raises LLMTransientError across retries, fallback engine executes."""
    findings = [
        Finding(
            title="SQL Injection in auth",
            cwe_id="CWE-89",
            cvss_score=Decimal("9.8"),
            severity="CRITICAL",
        )
    ]

    adapter = _FailingLLMAdapter()
    content, tokens_consumed, is_fallback = generate_ai_narrative(
        findings=findings,
        tone="EXECUTIVE",
        language="id",
        llm_adapter=adapter,
        retry_delay_seconds=0.001,  # fast backoff for testing
    )

    assert is_fallback is True
    assert tokens_consumed == 0
    assert "katalog CWE internal (EC-14)" in content.executive_summary
    assert len(content.remediations) == 1
    assert content.remediations[0].cwe_id == "CWE-89"
