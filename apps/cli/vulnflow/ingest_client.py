"""`vulnflow push` HTTP ingest client — PLAN.md FASE 5.6 (EC-07/EC-10).

EDGE_CASES_AND_RESILIENCE.md §5.5: the `Idempotency-Key` is a per-HTTP-request
gate, not a cross-fragment dedup mechanism — real data dedup still happens
server-side via `dedup_hash` (EC-08). It must be unique per chunk (so chunk 2
is never silently dropped as a "replay" of chunk 1) but stable across retries
of the *same* chunk (so a network retry of chunk 1 is recognized as the same
request, not a new one).
"""

import hashlib
import time
from collections.abc import Sequence
from pathlib import Path

import httpx

from vulnflow_contracts import (
    BatchIngestRequest,
    BatchIngestResponse,
    ScanMetadata,
    UnifiedVulnerabilityFinding,
)

MAX_ATTEMPTS = 3
DEFAULT_RETRY_DELAY_SECONDS = 1.0
_TRANSIENT_STATUS_CODES = {409, 429, 500, 502, 503, 504}
_FILE_HASH_CHUNK_BYTES = 1024 * 1024


class IngestTransientError(Exception):
    """Network error or transient server status, exhausted all retries."""


class FreeTierBatchLimitError(Exception):
    """HTTP 413 — EC-10: batch exceeds the account tier's per-batch limit."""


class IngestClientError(Exception):
    """Any other non-2xx response (auth, validation, scope, etc.)."""


def compute_file_hash(file_path: Path) -> str:
    digest = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(_FILE_HASH_CHUNK_BYTES), b""):
            digest.update(chunk)
    return digest.hexdigest()


def compute_idempotency_key(file_hash: str, chunk_index: int | None = None) -> str:
    if chunk_index is None:
        return file_hash
    return f"{file_hash}:{chunk_index}"


def chunk_findings[T](findings: Sequence[T], *, size: int = 500) -> list[list[T]]:
    return [list(findings[i : i + size]) for i in range(0, len(findings), size)]


def push_batch(
    client: httpx.Client,
    *,
    api_url: str,
    workspace_id: str,
    project_id: str,
    api_key: str,
    findings: list[UnifiedVulnerabilityFinding],
    scan_metadata: ScanMetadata,
    idempotency_key: str,
    retry_delay_seconds: float = DEFAULT_RETRY_DELAY_SECONDS,
) -> BatchIngestResponse:
    payload = BatchIngestRequest(scan_metadata=scan_metadata, findings=findings)
    url = f"{api_url}/api/v1/workspaces/{workspace_id}/projects/{project_id}/findings/batch"
    headers = {"X-VulnFlow-API-Key": api_key, "Idempotency-Key": idempotency_key}

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = client.post(url, json=payload.model_dump(mode="json"), headers=headers)
        except httpx.TransportError as exc:
            if attempt == MAX_ATTEMPTS:
                raise IngestTransientError(
                    f"Network error after {MAX_ATTEMPTS} attempts: {exc}"
                ) from exc
            time.sleep(retry_delay_seconds * (2 ** (attempt - 1)))
            continue

        if response.status_code == 413:
            detail = _error_message(response)
            raise FreeTierBatchLimitError(detail)

        if response.status_code in _TRANSIENT_STATUS_CODES:
            if attempt == MAX_ATTEMPTS:
                raise IngestTransientError(
                    f"Server returned {response.status_code} after {MAX_ATTEMPTS} attempts."
                )
            time.sleep(retry_delay_seconds * (2 ** (attempt - 1)))
            continue

        if response.status_code >= 400:
            raise IngestClientError(f"HTTP {response.status_code}: {_error_message(response)}")

        return BatchIngestResponse.model_validate(response.json())

    raise IngestTransientError(f"Exhausted {MAX_ATTEMPTS} attempts without a usable response.")


def _error_message(response: httpx.Response) -> str:
    try:
        body = response.json()
    except ValueError:
        return response.text
    return str(body.get("message", response.text))
