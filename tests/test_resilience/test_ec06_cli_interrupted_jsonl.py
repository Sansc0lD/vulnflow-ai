"""PLAN.md FASE 7.2 — EC-06: Scanner Interrupted Mid-Run (Ctrl+C) JSONL Resiliency.

EDGE_CASES_AND_RESILIENCE.md §5.1 & §6 item 6:
If a scanner (Nuclei) process is abruptly killed or terminated via `Ctrl+C` mid-write,
the resulting file ends with an incomplete, truncated JSON string fragment.
The streaming parser (`parse_nuclei_stream`) must gracefully recover every complete
finding preceding the interrupt, discarding only the corrupted trailing line
without crashing or raising JSONDecodeError.
"""

import json
from pathlib import Path

from vulnflow.parsers.nuclei_parser import normalize_nuclei_finding, parse_nuclei_stream


def _sample_nuclei_finding(template_id: str, name: str) -> dict:
    return {
        "template-id": template_id,
        "info": {
            "name": name,
            "severity": "high",
            "classification": {"cwe-id": ["cwe-89"], "cvss-score": 8.5},
        },
        "matched-at": "https://target.corp.com/api/v1/search",
        "host": "target.corp.com",
    }


def test_ec06_recovers_intact_findings_from_interrupted_jsonl(tmp_path: Path) -> None:
    """Interrupted stream with a half-written trailing line preserves prior findings."""
    log_file = tmp_path / "interrupted_scan.jsonl"
    f1 = _sample_nuclei_finding("cve-2023-0001", "Vulnerability Alpha")
    f2 = _sample_nuclei_finding("cve-2023-0002", "Vulnerability Beta")

    # Write two intact JSON lines, followed by a cut-off half line (interrupted mid-write)
    content = (
        json.dumps(f1)
        + "\n"
        + json.dumps(f2)
        + "\n"
        + '{"template-id": "cve-2023-0003", "info": {"name": "Cut-off Vulnerab'  # truncated!
    )
    log_file.write_text(content, encoding="utf-8")

    parsed = list(parse_nuclei_stream(log_file))
    assert len(parsed) == 2
    assert parsed[0]["template-id"] == "cve-2023-0001"
    assert parsed[1]["template-id"] == "cve-2023-0002"

    # Both findings can be normalized into UnifiedVulnerabilityFinding successfully
    norm1 = normalize_nuclei_finding(parsed[0])
    norm2 = normalize_nuclei_finding(parsed[1])
    assert norm1.title == "Vulnerability Alpha"
    assert norm2.title == "Vulnerability Beta"
    assert norm1.cwe_id == "CWE-89"


def test_ec06_recovers_interrupted_json_array_syntax(tmp_path: Path) -> None:
    """Scan started as an array `[...` but interrupted before closing bracket `]`."""
    log_file = tmp_path / "interrupted_array.json"
    f1 = _sample_nuclei_finding("sqli-test", "SQLi")
    f2 = _sample_nuclei_finding("xss-test", "XSS")

    # Array started with `[` but abruptly ended after second item without closing `]`
    content = f'[\n{json.dumps(f1)},\n{json.dumps(f2)},\n{{"template-id": "partial'
    log_file.write_text(content, encoding="utf-8")

    parsed = list(parse_nuclei_stream(log_file))
    assert len(parsed) == 2
    assert parsed[0]["template-id"] == "sqli-test"
    assert parsed[1]["template-id"] == "xss-test"
