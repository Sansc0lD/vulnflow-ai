"""AIGhostwriterService — SDD §2.2.3 (UC-11); EC-13/EC-14 guardrails.

Orchestrates `PromptSanitizationService` (never send raw PoC/target data to
an LLM), a retrying call to an injected LLM adapter, and a fallback to
`DeterministicFallbackEngine` when the adapter keeps failing (quota/timeout).
"""

import inspect
import time
from dataclasses import dataclass
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


@dataclass(slots=True)
class NarrativeGenerationResult:
    content: NarrativeContent
    tokens_consumed: int
    prompt_tokens: int
    candidates_tokens: int
    model_used: str | None
    is_fallback: bool


def _build_fallback_narrative(
    findings: list[Any], *, tech_stack: dict[str, str] | None = None
) -> NarrativeContent:
    remediations = [
        RemediationItem(
            cwe_id=finding.cwe_id,
            vuln_title=sanitize_text(finding.title),
            remediation_guidance=get_fallback_narrative(finding.cwe_id, tech_stack=tech_stack)[
                "remediation"
            ],
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


def _adapter_accepts_tech_stack(adapter: LLMAdapter) -> bool:
    try:
        sig = inspect.signature(adapter.generate_narrative)
    except (TypeError, ValueError):
        return False
    return "tech_stack" in sig.parameters


def generate_ai_narrative(
    findings: list[Any],
    *,
    tone: str,
    language: str,
    llm_adapter: LLMAdapter,
    retry_delay_seconds: float = DEFAULT_RETRY_DELAY_SECONDS,
    tech_stack: dict[str, str] | None = None,
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

    extra_kwargs: dict[str, Any] = {}
    if tech_stack and _adapter_accepts_tech_stack(llm_adapter):
        extra_kwargs["tech_stack"] = tech_stack

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            content, tokens_consumed = llm_adapter.generate_narrative(
                abstract_findings=abstract_findings,
                tone=tone,
                language=language,
                **extra_kwargs,
            )
            return content, tokens_consumed, False
        except LLMTransientError:
            if attempt == MAX_ATTEMPTS:
                break
            time.sleep(retry_delay_seconds * (2 ** (attempt - 1)))  # exponential backoff

    return _build_fallback_narrative(findings, tech_stack=tech_stack), 0, True


def generate_ai_narrative_detailed(
    findings: list[Any],
    *,
    tone: str,
    language: str,
    llm_adapter: LLMAdapter,
    retry_delay_seconds: float = DEFAULT_RETRY_DELAY_SECONDS,
    tech_stack: dict[str, str] | None = None,
) -> NarrativeGenerationResult:
    content, tokens_consumed, is_fallback = generate_ai_narrative(
        findings,
        tone=tone,
        language=language,
        llm_adapter=llm_adapter,
        retry_delay_seconds=retry_delay_seconds,
        tech_stack=tech_stack,
    )
    if is_fallback:
        return NarrativeGenerationResult(
            content=content,
            tokens_consumed=0,
            prompt_tokens=0,
            candidates_tokens=0,
            model_used="deterministic_fallback",
            is_fallback=True,
        )

    usage = getattr(llm_adapter, "last_usage", None)
    prompt_tokens = int(usage.get("prompt_tokens", 0)) if isinstance(usage, dict) else 0
    candidates_tokens = int(usage.get("candidates_tokens", 0)) if isinstance(usage, dict) else 0
    model_used = (
        str(usage.get("model_used"))
        if isinstance(usage, dict) and usage.get("model_used")
        else None
    )
    return NarrativeGenerationResult(
        content=content,
        tokens_consumed=tokens_consumed,
        prompt_tokens=prompt_tokens,
        candidates_tokens=candidates_tokens,
        model_used=model_used,
        is_fallback=False,
    )
