"""Nuclei JSON/JSONL parser & normalizer — PLAN.md FASE 5.5 (EC-06)."""

import json
from pathlib import Path

from vulnflow.parsers.nuclei_parser import normalize_nuclei_finding, parse_nuclei_stream

_SAMPLE_RAW = {
    "template-id": "sqli-detect",
    "info": {
        "name": "SQL Injection in login form",
        "severity": "critical",
        "classification": {
            "cwe-id": ["CWE-89"],
            "cvss-metrics": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
            "cvss-score": 9.8,
        },
    },
    "host": "https://target.example.com",
    "matched-at": "https://target.example.com:8443/api/v1/login",
    "type": "http",
}


def test_parse_nuclei_stream_reads_full_json_array(tmp_path: Path) -> None:
    file_path = tmp_path / "nuclei.json"
    file_path.write_text(json.dumps([_SAMPLE_RAW, _SAMPLE_RAW]), encoding="utf-8")

    items = list(parse_nuclei_stream(file_path))

    assert len(items) == 2
    assert items[0]["template-id"] == "sqli-detect"


def test_parse_nuclei_stream_reads_jsonl_lines(tmp_path: Path) -> None:
    file_path = tmp_path / "nuclei.jsonl"
    file_path.write_text(
        json.dumps(_SAMPLE_RAW) + "\n" + json.dumps(_SAMPLE_RAW) + "\n", encoding="utf-8"
    )

    items = list(parse_nuclei_stream(file_path))

    assert len(items) == 2


def test_parse_nuclei_stream_skips_corrupt_trailing_line(tmp_path: Path) -> None:
    # Simulates Ctrl+C truncating the scanner mid-write (EC-06): the last
    # line is a half-written JSON fragment, not valid JSON on its own.
    file_path = tmp_path / "nuclei_truncated.jsonl"
    file_path.write_text(
        json.dumps(_SAMPLE_RAW) + "\n" + '{"template-id": "truncated-mid-wri', encoding="utf-8"
    )

    items = list(parse_nuclei_stream(file_path))

    assert len(items) == 1
    assert items[0]["template-id"] == "sqli-detect"


def test_normalize_nuclei_finding_maps_core_fields() -> None:
    finding = normalize_nuclei_finding(_SAMPLE_RAW)

    assert finding.title == "SQL Injection in login form"
    assert finding.severity.value == "CRITICAL"
    assert finding.cwe_id == "CWE-89"
    assert finding.cvss_score == 9.8
    assert finding.cvss_vector == "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"
    assert finding.target_host == "target.example.com"
    assert finding.target_port == 8443
    assert finding.endpoint_path == "/api/v1/login"
    assert finding.source_tool.value == "nuclei"


def test_normalize_nuclei_finding_uppercases_real_world_lowercase_cwe_id() -> None:
    # Regression test: real Nuclei output emits lowercase `cwe-id` values
    # (confirmed by actually running a scan — e.g. "cwe-200", "cwe-693"), but
    # the contract's `cwe_id` field requires the pattern `^(CWE-[0-9]+|UNKNOWN)$`.
    # Every classified real-world finding was silently dropped by `push`
    # (caught by `except ValidationError: skipped += 1` in main.py) until this
    # was fixed — 8 of 10 findings from one real scan, in practice.
    raw = {
        "template-id": "http-missing-security-headers",
        "info": {
            "name": "Missing Security Headers",
            "severity": "info",
            "classification": {"cwe-id": ["cwe-693"]},
        },
        "host": "http://127.0.0.1:8000",
        "matched-at": "http://127.0.0.1:8000/",
    }

    finding = normalize_nuclei_finding(raw)

    assert finding.cwe_id == "CWE-693"


def test_normalize_nuclei_finding_defaults_when_classification_missing() -> None:
    raw = {
        "template-id": "tech-detect",
        "info": {"name": "Technology fingerprint", "severity": "info"},
        "host": "https://target.example.com",
        "matched-at": "https://target.example.com",
    }

    finding = normalize_nuclei_finding(raw)

    assert finding.cwe_id == "UNKNOWN"
    assert finding.cvss_score is None
    assert finding.cvss_vector is None
    assert finding.target_port is None


def test_normalize_nuclei_handles_schemeless_matched_at_with_port() -> None:
    raw = {
        "template-id": "openssh-detect",
        "info": {"name": "OpenSSH Banner", "severity": "info"},
        "host": "10.0.0.9:22",
        "matched-at": "10.0.0.9:22",
    }
    finding = normalize_nuclei_finding(raw)
    assert finding.target_host == "10.0.0.9"
    assert finding.target_port == 22
    assert finding.protocol.value == "tcp"
    assert finding.endpoint_path == ""
