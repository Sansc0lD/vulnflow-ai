"""OllamaLLMAdapter — Optional private VPC LLM backend for Enterprise deployments (#8)."""

from typing import Any

import httpx
from pydantic import ValidationError

from app.domain.ai_ghostwriter import LLMTransientError
from app.services.gemini_adapter import _build_prompt, _strip_json_fences
from vulnflow_contracts import NarrativeContent


class OllamaLLMAdapter:
    """Calls a self-hosted Ollama /api/chat endpoint while preserving Zero-PoC-to-AI."""

    def __init__(self, *, base_url: str, model: str, client: httpx.Client) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._client = client
        self.last_usage: dict[str, Any] = {
            "prompt_tokens": 0,
            "candidates_tokens": 0,
            "total_tokens": 0,
            "model_used": model,
        }

    def generate_narrative(
        self,
        *,
        abstract_findings: list[dict[str, Any]],
        tone: str,
        language: str,
        tech_stack: dict[str, str] | None = None,
    ) -> tuple[NarrativeContent, int]:
        prompt = _build_prompt(abstract_findings, tone, language, tech_stack=tech_stack)
        url = f"{self._base_url}/api/chat"
        try:
            response = self._client.post(
                url,
                json={
                    "model": self._model,
                    "stream": False,
                    "format": "json",
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
        except httpx.TimeoutException as exc:
            raise LLMTransientError("Ollama request timed out.") from exc
        except httpx.TransportError as exc:
            raise LLMTransientError("Ollama request failed at the transport layer.") from exc

        if response.status_code >= 400:
            raise LLMTransientError(f"Ollama returned status {response.status_code}.")

        try:
            data = response.json()
            text = str(data["message"]["content"])
            narrative = NarrativeContent.model_validate_json(_strip_json_fences(text))
            prompt_tokens = int(data.get("prompt_eval_count", 0) or 0)
            candidates_tokens = int(data.get("eval_count", 0) or 0)
            total_tokens = prompt_tokens + candidates_tokens
        except (KeyError, TypeError, ValueError, ValidationError) as exc:
            raise LLMTransientError("Ollama response could not be parsed.") from exc

        self.last_usage = {
            "prompt_tokens": prompt_tokens,
            "candidates_tokens": candidates_tokens,
            "total_tokens": total_tokens,
            "model_used": f"ollama:{self._model}",
        }
        return narrative, total_tokens
