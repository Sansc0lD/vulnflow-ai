"""AIGhostwriterService — SDD §2.2.3 (UC-11); EC-13/EC-14 guardrails.

Orchestrates `PromptSanitizationService` (never send raw PoC/target data to
an LLM), a retrying call to an injected LLM adapter, and a fallback to
`DeterministicFallbackEngine` when the adapter keeps failing (quota/timeout).
"""

import time
from typing import Any, Protocol

from app.domain.fallback import get_fallback_narrative
from app.domain.sanitizer import sanitize_text, whitelist_finding_metadata
from vulnflow_contracts import NarrativeContent, RemediationItem

MAX_ATTEMPTS = 3
DEFAULT_RETRY_DELAY_SECONDS = 1.0


class LLMTransientError(Exception):
    """Raised by an LLM adapter on 429/timeout — triggers retry, then fallback."""


class LLMAdapter(Protocol):
    def generate_narrative(
        self, *, abstract_findings: list[dict[str, Any]], tone: str, language: str
    ) -> tuple[NarrativeContent, int]: ...


def _build_fallback_narrative(findings: list[Any]) -> NarrativeContent:
    remediations = [
        RemediationItem(
            cwe_id=finding.cwe_id,
            vuln_title=sanitize_text(finding.title),
            remediation_guidance=get_fallback_narrative(finding.cwe_id)["remediation"],
        )
        for finding in findings
    ]
    return NarrativeContent(
        executive_summary=(
            "AI narrative generation is currently unavailable; this report uses a deterministic "
            "summary derived from the internal CWE catalog (EC-14)."
        ),
        business_impact=get_fallback_narrative(findings[0].cwe_id)["business_impact"],
        remediations=remediations,
    )


def generate_ai_narrative(
    findings: list[Any],
    *,
    tone: str,
    language: str,
    llm_adapter: LLMAdapter,
    retry_delay_seconds: float = DEFAULT_RETRY_DELAY_SECONDS,
) -> tuple[NarrativeContent, int, bool]:
    if not findings:
        raise ValueError("generate_ai_narrative requires at least one finding.")

    # F4-HIGH-14: sanitize_text strips IPs, hostnames, and URLs from finding titles
    # before sending to LLM
    abstract_findings = [
        whitelist_finding_metadata(
            {
                "title": sanitize_text(f.title),
                "cwe_id": f.cwe_id,
                "cvss_score": float(f.cvss_score),  # ORM uses Decimal; adapter/JSON wants float
                "severity": f.severity,
            }
        )
        for f in findings
    ]

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            content, tokens_consumed = llm_adapter.generate_narrative(
                abstract_findings=abstract_findings, tone=tone, language=language
            )
            return content, tokens_consumed, False
        except LLMTransientError:
            if attempt == MAX_ATTEMPTS:
                break
            time.sleep(retry_delay_seconds * (2 ** (attempt - 1)))  # exponential backoff

    return _build_fallback_narrative(findings), 0, True
