"""GeminiLLMAdapter — SDD UC-11 `GeminiClient` component.

Calls Gemini's REST API directly via `httpx` (no extra SDK dependency —
consistent with this project's existing use of `httpx` everywhere else).
`client` is injectable so tests run fully offline via `httpx.MockTransport`.

Only the abstract (already-sanitized) finding metadata is ever placed in
the prompt — see `_build_prompt`, which picks exactly four known-safe keys
rather than serializing whatever dict it's handed (defense-in-depth for
Zero-PoC-to-AI, in case a caller's whitelist step is ever bypassed upstream).
"""

import json
import os
from typing import Any

import httpx
from pydantic import ValidationError

from app.domain.ai_ghostwriter import LLMTransientError
from vulnflow_contracts import NarrativeContent

_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
_TRANSIENT_STATUS_CODES = {429, 500, 502, 503, 504}
DEFAULT_GEMINI_MODEL = "gemini-3-flash-preview"
DEFAULT_GEMINI_FALLBACK_MODEL = "gemini-2.5-flash-lite"

_RESPONSE_SCHEMA_INSTRUCTIONS = (
    "Respond with ONLY a JSON object matching this exact shape, no markdown "
    'fences, no extra text: {"executive_summary": str, "business_impact": '
    'str, "remediations": [{"cwe_id": str, "vuln_title": str, '
    '"remediation_guidance": str}]}'
)


def _build_prompt(
    abstract_findings: list[dict[str, Any]],
    tone: str,
    language: str,
    tech_stack: dict[str, str] | None = None,
) -> str:
    safe_findings = [
        {
            "title": f.get("title"),
            "cwe_id": f.get("cwe_id"),
            "cvss_score": f.get("cvss_score"),
            "severity": f.get("severity"),
        }
        for f in abstract_findings
    ]
    stack_line = ""
    if tech_stack:
        parts = [f"{k}={v}" for k, v in sorted(tech_stack.items()) if v]
        if parts:
            stack_line = f"Target Architecture Stack (abstract tags only): {', '.join(parts)}.\n"
    return (
        f"Tone: {tone}. Language: {language}.\n"
        f"{stack_line}"
        f"Findings (abstract metadata only): {json.dumps(safe_findings)}\n"
        f"{_RESPONSE_SCHEMA_INSTRUCTIONS}"
    )


def _strip_json_fences(raw_text: str) -> str:
    stripped = raw_text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        return "\n".join(lines).strip()
    return stripped


class GeminiLLMAdapter:
    def __init__(
        self,
        *,
        api_key: str,
        model: str | None = None,
        client: httpx.Client,
        fallback_model: str | None = None,
    ) -> None:
        self._api_key = api_key
        self._model = model or os.environ.get("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)
        self._fallback_model = (
            fallback_model
            if fallback_model is not None
            else os.environ.get("GEMINI_FALLBACK_MODEL", DEFAULT_GEMINI_FALLBACK_MODEL)
        )
        self._client = client
        self.last_usage: dict[str, Any] = {
            "prompt_tokens": 0,
            "candidates_tokens": 0,
            "total_tokens": 0,
            "model_used": self._model,
        }

    def _call_model(self, model_name: str, prompt: str) -> httpx.Response:
        url = f"{_API_BASE_URL}/{model_name}:generateContent"
        try:
            # F4-MED-17: send API key via header to avoid logging key in query params
            return self._client.post(
                url,
                headers={"x-goog-api-key": self._api_key},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"responseMimeType": "application/json"},
                },
            )
        except httpx.TimeoutException as exc:
            raise LLMTransientError("Gemini request timed out.") from exc
        except httpx.TransportError as exc:
            raise LLMTransientError("Gemini request failed at the transport layer.") from exc

    def generate_narrative(
        self,
        *,
        abstract_findings: list[dict[str, Any]],
        tone: str,
        language: str,
        tech_stack: dict[str, str] | None = None,
    ) -> tuple[NarrativeContent, int]:
        if not self._api_key or not self._api_key.strip():
            raise LLMTransientError("Gemini API key is not configured.")

        prompt = _build_prompt(abstract_findings, tone, language, tech_stack=tech_stack)
        active_model = self._model
        response = self._call_model(active_model, prompt)

        if (
            response.status_code in {429, 503}
            and self._fallback_model
            and self._fallback_model != active_model
        ):
            active_model = self._fallback_model
            response = self._call_model(active_model, prompt)

        if response.status_code in _TRANSIENT_STATUS_CODES or response.status_code >= 400:
            raise LLMTransientError(f"Gemini returned status {response.status_code}.")

        try:
            data = response.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            narrative = NarrativeContent.model_validate_json(_strip_json_fences(text))
            usage = data.get("usageMetadata", {}) or {}
            prompt_tokens = int(usage.get("promptTokenCount", 0) or 0)
            candidates_tokens = int(usage.get("candidatesTokenCount", 0) or 0)
            tokens_consumed = int(
                usage.get("totalTokenCount", prompt_tokens + candidates_tokens) or 0
            )
        except (KeyError, IndexError, ValueError, ValidationError) as exc:
            raise LLMTransientError("Gemini response could not be parsed.") from exc

        self.last_usage = {
            "prompt_tokens": prompt_tokens,
            "candidates_tokens": candidates_tokens,
            "total_tokens": tokens_consumed,
            "model_used": active_model,
        }
        return narrative, tokens_consumed
