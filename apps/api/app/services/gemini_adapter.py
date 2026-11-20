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
from typing import Any

import httpx
from pydantic import ValidationError

from app.domain.ai_ghostwriter import LLMTransientError
from vulnflow_contracts import NarrativeContent

_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
_TRANSIENT_STATUS_CODES = {429, 500, 502, 503, 504}

_RESPONSE_SCHEMA_INSTRUCTIONS = (
    "Respond with ONLY a JSON object matching this exact shape, no markdown "
    'fences, no extra text: {"executive_summary": str, "business_impact": '
    'str, "remediations": [{"cwe_id": str, "vuln_title": str, '
    '"remediation_guidance": str}]}'
)


def _build_prompt(abstract_findings: list[dict[str, Any]], tone: str, language: str) -> str:
    safe_findings = [
        {
            "title": f.get("title"),
            "cwe_id": f.get("cwe_id"),
            "cvss_score": f.get("cvss_score"),
            "severity": f.get("severity"),
        }
        for f in abstract_findings
    ]
    return (
        f"Tone: {tone}. Language: {language}.\n"
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
    def __init__(self, *, api_key: str, model: str, client: httpx.Client) -> None:
        self._api_key = api_key
        self._model = model
        self._client = client

    def generate_narrative(
        self, *, abstract_findings: list[dict[str, Any]], tone: str, language: str
    ) -> tuple[NarrativeContent, int]:
        if not self._api_key or not self._api_key.strip():
            raise LLMTransientError("Gemini API key is not configured.")

        prompt = _build_prompt(abstract_findings, tone, language)
        url = f"{_API_BASE_URL}/{self._model}:generateContent"

        try:
            # F4-MED-17: send API key via header to avoid logging key in query params
            response = self._client.post(
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

        if response.status_code in _TRANSIENT_STATUS_CODES or response.status_code >= 400:
            raise LLMTransientError(f"Gemini returned status {response.status_code}.")

        try:
            data = response.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            narrative = NarrativeContent.model_validate_json(_strip_json_fences(text))
            tokens_consumed = int(data.get("usageMetadata", {}).get("totalTokenCount", 0))
        except (KeyError, IndexError, ValueError, ValidationError) as exc:
            raise LLMTransientError("Gemini response could not be parsed.") from exc

        return narrative, tokens_consumed
