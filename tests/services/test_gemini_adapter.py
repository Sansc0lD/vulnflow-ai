"""PLAN.md FASE 4.6 — GeminiLLMAdapter (SDD UC-11 GeminiClient; EC-14)."""

import json

import httpx
import pytest
from app.domain.ai_ghostwriter import LLMTransientError
from app.services.gemini_adapter import GeminiLLMAdapter

_ABSTRACT_FINDINGS = [
    {"title": "SQLi", "cwe_id": "CWE-89", "cvss_score": 9.8, "severity": "CRITICAL"}
]


def _client_with_response(status_code: int, json_body: dict[str, object]) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, json=json_body)

    return httpx.Client(transport=httpx.MockTransport(handler))


def _gemini_success_body(narrative_json: dict[str, object], token_count: int) -> dict[str, object]:
    return {
        "candidates": [{"content": {"parts": [{"text": json.dumps(narrative_json)}]}}],
        "usageMetadata": {"totalTokenCount": token_count},
    }


def test_generate_narrative_parses_successful_response() -> None:
    narrative = {
        "executive_summary": "Ringkasan eksekutif.",
        "business_impact": "Dampak signifikan.",
        "remediations": [
            {"cwe_id": "CWE-89", "vuln_title": "SQLi", "remediation_guidance": "Use params."}
        ],
    }
    client = _client_with_response(200, _gemini_success_body(narrative, 456))
    adapter = GeminiLLMAdapter(api_key="k", model="gemini-2.0-flash", client=client)

    content, tokens = adapter.generate_narrative(
        abstract_findings=_ABSTRACT_FINDINGS, tone="formal_executive", language="id"
    )

    assert content.executive_summary == "Ringkasan eksekutif."
    assert tokens == 456


def test_generate_narrative_raises_transient_error_on_429() -> None:
    client = _client_with_response(429, {"error": "rate limited"})
    adapter = GeminiLLMAdapter(api_key="k", model="gemini-2.0-flash", client=client)

    with pytest.raises(LLMTransientError):
        adapter.generate_narrative(
            abstract_findings=_ABSTRACT_FINDINGS, tone="formal_executive", language="id"
        )


def test_generate_narrative_raises_transient_error_on_503() -> None:
    client = _client_with_response(503, {"error": "unavailable"})
    adapter = GeminiLLMAdapter(api_key="k", model="gemini-2.0-flash", client=client)

    with pytest.raises(LLMTransientError):
        adapter.generate_narrative(
            abstract_findings=_ABSTRACT_FINDINGS, tone="formal_executive", language="id"
        )


def test_generate_narrative_raises_transient_error_on_timeout() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("timed out")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    adapter = GeminiLLMAdapter(api_key="k", model="gemini-2.0-flash", client=client)

    with pytest.raises(LLMTransientError):
        adapter.generate_narrative(
            abstract_findings=_ABSTRACT_FINDINGS, tone="formal_executive", language="id"
        )


def test_generate_narrative_raises_transient_error_on_malformed_json() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        part = {"text": "not valid json{{{"}
        content = {"parts": [part]}
        candidate = {"content": content}
        body = {"candidates": [candidate]}
        return httpx.Response(200, json=body)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    adapter = GeminiLLMAdapter(api_key="k", model="gemini-2.0-flash", client=client)

    with pytest.raises(LLMTransientError):
        adapter.generate_narrative(
            abstract_findings=_ABSTRACT_FINDINGS, tone="formal_executive", language="id"
        )


def test_generate_narrative_never_sends_target_host_or_poc_in_request_body() -> None:
    # Zero-PoC-to-AI: even if the caller somehow slipped extra keys into the
    # abstract_findings dicts, only the known-safe prompt text is built —
    # this test locks that structural guarantee in place.
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = request.content.decode("utf-8")
        narrative = {"executive_summary": "x", "business_impact": "x", "remediations": []}
        return httpx.Response(200, json=_gemini_success_body(narrative, 1))

    client = httpx.Client(transport=httpx.MockTransport(handler))
    adapter = GeminiLLMAdapter(api_key="k", model="gemini-2.0-flash", client=client)

    sneaky_findings = [
        {
            "title": "SQLi",
            "cwe_id": "CWE-89",
            "cvss_score": 9.8,
            "severity": "CRITICAL",
            "target_host": "internal-db.klien.local",
        }
    ]
    adapter.generate_narrative(
        abstract_findings=sneaky_findings, tone="formal_executive", language="id"
    )

    assert "internal-db.klien.local" not in str(captured["body"])


def test_gemini_adapter_sends_api_key_in_header_not_query_param() -> None:
    # F4-MED-17: API key must be in x-goog-api-key header, not logged in query params
    captured_request: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_request["headers"] = dict(request.headers)
        captured_request["url_query"] = str(request.url.query)
        narrative = {"executive_summary": "x", "business_impact": "x", "remediations": []}
        return httpx.Response(200, json=_gemini_success_body(narrative, 1))

    client = httpx.Client(transport=httpx.MockTransport(handler))
    adapter = GeminiLLMAdapter(
        api_key="secret-api-key-12345", model="gemini-2.0-flash", client=client
    )

    adapter.generate_narrative(
        abstract_findings=_ABSTRACT_FINDINGS, tone="formal_executive", language="id"
    )

    headers = captured_request.get("headers", {})
    assert isinstance(headers, dict)
    assert headers.get("x-goog-api-key") == "secret-api-key-12345"
    assert "key=secret-api-key-12345" not in str(captured_request.get("url_query"))
