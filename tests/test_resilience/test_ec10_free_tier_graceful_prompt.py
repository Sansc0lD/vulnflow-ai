"""PLAN.md FASE 7.2 — EC-10: Free Tier Batch Limit Graceful Degradation.

EDGE_CASES_AND_RESILIENCE.md §6 item 10:
When an auditor on a FREE subscription plan attempts to push a batch containing
more than 50 findings, the backend responds with HTTP 413 (PAYLOAD_TOO_LARGE).
Rather than abruptly terminating with an error, the CLI interactively prompts
the user to truncate and upload only the top 50 findings gracefully.
"""

from pathlib import Path

import pytest
import vulnflow.main as main_module
from typer.testing import CliRunner
from vulnflow.config import CLIConfig
from vulnflow.ingest_client import FreeTierBatchLimitError
from vulnflow.main import app

from vulnflow_contracts import BatchIngestResponse

runner = CliRunner()


@pytest.fixture(autouse=True)
def _stub_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        main_module,
        "load_config",
        lambda: CLIConfig(
            api_url="https://api.vulnflow.ai",
            api_key="vf_live_free_key",
            active_workspace_id="wsp-free-01",
        ),
    )


def test_ec10_free_tier_50_cap_prompt_accepted_retries_top_50(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When HTTP 413 occurs and user confirms 'y', CLI retries with top 50 findings."""
    call_log = []

    def _fake_push_batch(*args, findings, **kwargs):
        call_log.append(len(findings))
        if len(call_log) == 1:
            raise FreeTierBatchLimitError("Batch of 52 findings exceeds Free tier limit of 50.")
        return BatchIngestResponse(
            new_findings_count=50, duplicate_findings_count=0, quarantined_count=0
        )

    monkeypatch.setattr(main_module, "push_batch", _fake_push_batch)

    # Create dummy scan file
    scan_file = tmp_path / "large_scan.jsonl"
    line = (
        '{"template-id": "sqli", "info": {"name": "SQL Injection", "severity": "high"}, '
        '"host": "target.com"}\n'
    )
    scan_file.write_text(line * 52, encoding="utf-8")

    result = runner.invoke(
        app,
        ["push", "--project", "prj-01", "--type", "nuclei", "--file", str(scan_file)],
        input="y\n",
    )

    assert result.exit_code == 0
    assert len(call_log) == 2
    assert call_log[0] == 52  # first attempt: all 52 findings -> rejected
    assert call_log[1] == 50  # second attempt: truncated to top 50 -> accepted
    assert "50 new" in result.stdout


def test_ec10_free_tier_prompt_declined_cancels_cleanly(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When HTTP 413 occurs and user inputs 'n', CLI exits cleanly without upload."""

    def _fake_push_batch(*args, **kwargs):
        raise FreeTierBatchLimitError("Batch of 52 findings exceeds Free tier limit of 50.")

    monkeypatch.setattr(main_module, "push_batch", _fake_push_batch)

    scan_file = tmp_path / "large_scan.jsonl"
    line = (
        '{"template-id": "sqli", "info": {"name": "SQL Injection", "severity": "high"}, '
        '"host": "target.com"}\n'
    )
    scan_file.write_text(line * 52, encoding="utf-8")

    result = runner.invoke(
        app,
        ["push", "--project", "prj-01", "--type", "nuclei", "--file", str(scan_file)],
        input="n\n",
    )

    assert result.exit_code == 1
    assert "Upload cancelled" in result.stdout or result.exit_code != 0
