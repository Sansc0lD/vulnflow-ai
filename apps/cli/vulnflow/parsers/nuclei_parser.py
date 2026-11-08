"""Nuclei JSON/JSONL parser & normalizer — PLAN.md FASE 5.5 (EC-06).

EDGE_CASES_AND_RESILIENCE.md §5.1: Nuclei's `-json` output is a full JSON
array under normal completion, but a scan interrupted mid-write (`Ctrl+C`)
leaves a file that is neither valid JSON nor valid JSON Lines at its very
last line — only that trailing fragment is corrupt, and every finding
written before the interruption is still intact. `parse_nuclei_stream`
therefore tries whole-array parsing first and falls back to line-by-line
streaming (skipping only the lines that fail to parse) so a truncated file
never loses the findings that *did* complete.
"""

import json
import urllib.parse
from collections.abc import Generator
from pathlib import Path
from typing import Any

from vulnflow_contracts import (
    ProofOfConceptSchema,
    Protocol,
    Severity,
    SourceTool,
    UnifiedVulnerabilityFinding,
)

_SEVERITY_MAP = {s.value.lower(): s for s in Severity}
_RAW_EVIDENCE_MAX_CHARS = 100_000


def parse_nuclei_stream(file_path: Path) -> Generator[dict[str, Any], None, None]:
    with file_path.open("r", encoding="utf-8", errors="ignore") as f:
        content = f.read().strip()
        if content.startswith("[") and content.endswith("]"):
            try:
                yield from json.loads(content)
                return
            except json.JSONDecodeError:
                pass  # Fall through to line-by-line streaming below.

        for line in content.splitlines():
            line_str = line.strip().rstrip(",")
            if not line_str or line_str in {"[", "]"}:
                continue
            try:
                yield json.loads(line_str)
            except json.JSONDecodeError:
                continue  # EC-06: skip a corrupt trailing fragment, not the whole file.


def normalize_nuclei_finding(raw: dict[str, Any]) -> UnifiedVulnerabilityFinding:
    info = raw.get("info") or {}
    classification = info.get("classification") or {}

    severity = _SEVERITY_MAP.get(str(info.get("severity", "")).lower(), Severity.INFO)
    cwe_ids = classification.get("cwe-id") or []
    # Real Nuclei output emits lowercase ("cwe-200"), but the contract
    # requires `^(CWE-[0-9]+|UNKNOWN)$` — confirmed by running a real scan,
    # where every classified finding was silently dropped without this.
    cwe_id = cwe_ids[0].upper() if cwe_ids else "UNKNOWN"

    matched_at = raw.get("matched-at") or raw.get("host") or ""
    parsed_url = urllib.parse.urlsplit(matched_at)
    target_host = parsed_url.hostname or str(raw.get("host", ""))
    protocol = Protocol.HTTP if parsed_url.scheme == "http" else Protocol.HTTPS
    if parsed_url.scheme not in {"http", "https"}:
        protocol = Protocol.OTHER

    template_id = raw.get("template-id", "unknown-template")
    raw_evidence = json.dumps(raw, ensure_ascii=False)[:_RAW_EVIDENCE_MAX_CHARS]

    return UnifiedVulnerabilityFinding(
        title=info.get("name") or template_id,
        severity=severity,
        cvss_score=classification.get("cvss-score"),
        cvss_vector=classification.get("cvss-metrics"),
        cwe_id=cwe_id,
        target_host=target_host,
        target_port=parsed_url.port,
        endpoint_path=parsed_url.path or "",
        protocol=protocol,
        source_tool=SourceTool.NUCLEI,
        proof_of_concept=ProofOfConceptSchema(
            raw_evidence=raw_evidence,
            reproduction_steps=[f"Nuclei template '{template_id}' matched at {matched_at}"],
        ),
    )
