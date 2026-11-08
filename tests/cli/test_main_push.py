"""`vulnflow push` command wiring — PLAN.md FASE 5.6 (EC-07/EC-10)."""

import json
from pathlib import Path

import pytest
import vulnflow.main as main_module
from typer.testing import CliRunner
from vulnflow.config import CLIConfig
from vulnflow.ingest_client import FreeTierBatchLimitError
from vulnflow.main import app

from vulnflow_contracts import BatchIngestResponse

runner = CliRunner()

_NUCLEI_LINE = {
    "template-id": "tech-detect",
    "info": {"name": "Tech fingerprint", "severity": "info"},
    "host": "https://target.example.com",
    "matched-at": "https://target.example.com",
}


@pytest.fixture(autouse=True)
def _stub_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        main_module,
        "load_config",
        lambda: CLIConfig(
            api_url="https://api.vulnflow.ai",
            api_key="vf_live_test",
            active_workspace_id="wsp-01",
        ),
    )


def _nuclei_file(tmp_path: Path, n: int = 1) -> Path:
    file_path = tmp_path / "scan.jsonl"
    file_path.write_text("\n".join(json.dumps(_NUCLEI_LINE) for _ in range(n)), encoding="utf-8")
    return file_path


def test_push_reports_success_counts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        main_module,
        "push_batch",
        lambda *args, **kwargs: BatchIngestResponse(
            new_findings_count=1, duplicate_findings_count=0, quarantined_count=0
        ),
    )
    file_path = _nuclei_file(tmp_path)

    result = runner.invoke(
        app, ["push", "--project", "prj-01", "--type", "nuclei", "--file", str(file_path)]
    )

    assert result.exit_code == 0
    assert "1 new" in result.stdout


def test_push_fails_cleanly_when_not_configured(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from vulnflow.config import ConfigNotFoundError

    def _raise() -> None:
        raise ConfigNotFoundError("Run `vulnflow configure` first.")

    monkeypatch.setattr(main_module, "load_config", _raise)
    file_path = _nuclei_file(tmp_path)

    result = runner.invoke(
        app, ["push", "--project", "prj-01", "--type", "nuclei", "--file", str(file_path)]
    )

    assert result.exit_code == 1


def test_push_exits_cleanly_when_file_has_no_valid_findings(tmp_path: Path) -> None:
    file_path = tmp_path / "empty.jsonl"
    file_path.write_text("", encoding="utf-8")

    result = runner.invoke(
        app, ["push", "--project", "prj-01", "--type", "nuclei", "--file", str(file_path)]
    )

    assert result.exit_code == 1


def test_push_rejects_unsupported_scan_type(tmp_path: Path) -> None:
    file_path = _nuclei_file(tmp_path)

    result = runner.invoke(
        app, ["push", "--project", "prj-01", "--type", "masscan", "--file", str(file_path)]
    )

    assert result.exit_code != 0


def test_push_free_tier_prompt_accepted_retries_with_top_50(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = {"count": 0}

    def _fake_push_batch(*args: object, **kwargs: object) -> BatchIngestResponse:
        calls["count"] += 1
        if calls["count"] == 1:
            raise FreeTierBatchLimitError("Free tier is limited to 50 findings per batch.")
        return BatchIngestResponse(
            new_findings_count=1, duplicate_findings_count=0, quarantined_count=0
        )

    monkeypatch.setattr(main_module, "push_batch", _fake_push_batch)
    file_path = _nuclei_file(tmp_path)

    result = runner.invoke(
        app,
        ["push", "--project", "prj-01", "--type", "nuclei", "--file", str(file_path)],
        input="y\n",
    )

    assert result.exit_code == 0
    assert calls["count"] == 2
    assert "1 new" in result.stdout


def test_push_free_tier_prompt_declined_aborts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _fake_push_batch(*args: object, **kwargs: object) -> BatchIngestResponse:
        raise FreeTierBatchLimitError("Free tier is limited to 50 findings per batch.")

    monkeypatch.setattr(main_module, "push_batch", _fake_push_batch)
    file_path = _nuclei_file(tmp_path)

    result = runner.invoke(
        app,
        ["push", "--project", "prj-01", "--type", "nuclei", "--file", str(file_path)],
        input="n\n",
    )

    assert result.exit_code == 1
