"""Regression tests for v1.0.0 CLI hardening."""

import io
import json
import zipfile
from pathlib import Path

import httpx
import pytest
from typer.testing import CliRunner
from vulnflow.config import normalize_api_url
from vulnflow.ingest_client import IngestClientError, push_batch
from vulnflow.main import app
from vulnflow.parsers.nuclei_parser import normalize_nuclei_finding
from vulnflow.tool_provisioner import ToolProvisioningError, ensure_tools_installed

from vulnflow_contracts import ScanMetadata

_RUNNER = CliRunner()


def test_normalize_api_url_strips_trailing_slashes_and_api_suffixes() -> None:
    assert normalize_api_url("http://localhost:8000/") == "http://localhost:8000"
    assert normalize_api_url("http://localhost:8000/api/v1/") == "http://localhost:8000"
    assert normalize_api_url("https://api.example.com/api") == "https://api.example.com"


def test_push_batch_normalizes_api_url_before_request() -> None:
    seen_urls: list[str] = []

    def _handler(request: httpx.Request) -> httpx.Response:
        seen_urls.append(str(request.url))
        return httpx.Response(
            201,
            json={
                "new_findings_count": 1,
                "duplicate_findings_count": 0,
                "quarantined_count": 0,
                "reopened_findings_count": 0,
            },
        )

    finding = normalize_nuclei_finding(
        {
            "template-id": "test-tmpl",
            "host": "https://app.example.com",
            "matched-at": "https://app.example.com/login",
            "info": {
                "name": "Test Finding",
                "severity": "medium",
                "classification": {"cwe-id": ["cwe-200"], "cvss-score": 5.3},
            },
        }
    )
    client = httpx.Client(transport=httpx.MockTransport(_handler))
    res = push_batch(
        client,
        api_url="http://localhost:8000/api/v1/",
        workspace_id="w1",
        project_id="p1",
        api_key="vf_key",
        findings=[finding],
        scan_metadata=ScanMetadata(
            scanner_name="nuclei", scanner_version="v3", scan_duration_seconds=1.0
        ),
        idempotency_key="hash-1",
    )
    assert res.new_findings_count == 1
    assert seen_urls == ["http://localhost:8000/api/v1/workspaces/w1/projects/p1/findings/batch"]


def test_nuclei_parser_drops_non_v31_cvss_vector_instead_of_skipping() -> None:
    finding = normalize_nuclei_finding(
        {
            "template-id": "v30-vector",
            "host": "https://app.example.com",
            "matched-at": "https://app.example.com/health",
            "info": {
                "name": "CVSS 3.0 Vector Template",
                "severity": "low",
                "classification": {
                    "cwe-id": ["CWE-200"],
                    "cvss-score": 3.7,
                    "cvss-metrics": "CVSS:3.0/AV:N/AC:H/PR:N/UI:N/S:U/C:L/I:N/A:N",
                },
            },
        }
    )
    assert finding.cvss_score == 3.7
    assert finding.cvss_vector is None


def test_tool_provisioner_wraps_bad_json_and_corrupt_zip(tmp_path: Path) -> None:
    bad_json_client = httpx.Client(
        transport=httpx.MockTransport(lambda _r: httpx.Response(200, json={"no_tag": True}))
    )
    with pytest.raises(ToolProvisioningError, match="Unexpected GitHub releases API response"):
        ensure_tools_installed(tmp_path / "b1", client=bad_json_client)

    bad_zip_client = httpx.Client(
        transport=httpx.MockTransport(
            lambda req: (
                httpx.Response(200, json={"tag_name": "v3.2.0"})
                if "api.github.com" in str(req.url)
                else httpx.Response(200, content=b"not-a-zip")
            )
        )
    )
    with pytest.raises(ToolProvisioningError, match="corrupted or not a valid zip file"):
        ensure_tools_installed(tmp_path / "b2", client=bad_zip_client)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("other.txt", "hi")
    missing_bin_client = httpx.Client(
        transport=httpx.MockTransport(
            lambda req: (
                httpx.Response(200, json={"tag_name": "v3.2.0"})
                if "api.github.com" in str(req.url)
                else httpx.Response(200, content=buf.getvalue())
            )
        )
    )
    with pytest.raises(ToolProvisioningError, match="does not contain"):
        ensure_tools_installed(tmp_path / "b3", client=missing_bin_client)


def test_cli_push_handles_malformed_nmap_xml_and_top50_retry_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text(
        json.dumps(
            {
                "api_url": "http://localhost:8000",
                "api_key": "vf_test_12345678",
                "active_workspace_id": "w1",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "vulnflow.main.load_config",
        lambda: __import__("vulnflow.config", fromlist=["load_config"]).load_config(path=cfg_path),
    )

    bad_xml = tmp_path / "bad.xml"
    bad_xml.write_text("<nmaprun><broken", encoding="utf-8")
    res_xml = _RUNNER.invoke(
        app, ["push", "--project", "p1", "--type", "nmap", "--file", str(bad_xml)]
    )
    assert res_xml.exit_code == 1
    assert "Failed to parse Nmap XML" in res_xml.output

    scan_jsonl = tmp_path / "scan.jsonl"
    scan_jsonl.write_text(
        json.dumps(
            {
                "template-id": "t1",
                "host": "https://app.example.com",
                "matched-at": "https://app.example.com/",
                "info": {"name": "F1", "severity": "high"},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    calls = 0

    def _fake_push(*args: object, **kwargs: object) -> object:
        nonlocal calls
        calls += 1
        if calls == 1:
            from vulnflow.ingest_client import FreeTierBatchLimitError

            raise FreeTierBatchLimitError("Too many findings")
        raise IngestClientError("HTTP 401: revoked")

    monkeypatch.setattr("vulnflow.main.push_batch", _fake_push)
    res_push = _RUNNER.invoke(
        app,
        ["push", "--project", "p1", "--type", "nuclei", "--file", str(scan_jsonl)],
        input="y\n",
    )
    assert res_push.exit_code == 1
    assert "Upload failed: HTTP 401: revoked" in res_push.output
