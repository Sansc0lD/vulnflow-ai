"""`vulnflow scan` command wiring — PLAN.md FASE 5.4."""

from pathlib import Path

import pytest
import vulnflow.main as main_module
from typer.testing import CliRunner
from vulnflow.environment import TargetEnvironment
from vulnflow.main import app
from vulnflow.scanner import ScanExecutionError

runner = CliRunner()

_FIXED_ENV = TargetEnvironment(
    os_tag="linux",
    arch_tag="amd64",
    extension=".zip",
    binary_name="nuclei",
)


@pytest.fixture(autouse=True)
def _fixed_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    # The real OS/arch this suite happens to run on is irrelevant to what
    # `scan` does with a resolved environment — pin it so `binary_name` (and
    # thus the expected binary path) is deterministic across CI platforms.
    monkeypatch.setattr(main_module, "resolve_target_environment", lambda: _FIXED_ENV)


def test_scan_fails_when_binary_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    missing_binary = tmp_path / "nuclei"
    monkeypatch.setattr(main_module, "get_default_install_dir", lambda: tmp_path)

    result = runner.invoke(
        app,
        ["scan", "--target", "https://target.example.com", "--output", str(tmp_path / "out.jsonl")],
    )

    assert result.exit_code == 1
    combined_output = result.stdout + (result.stderr if result.stderr_bytes is not None else "")
    assert "setup-tools" in combined_output
    assert not missing_binary.exists()


def test_scan_succeeds_when_binary_present(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    binary = tmp_path / "nuclei"
    binary.write_bytes(b"fake")
    monkeypatch.setattr(main_module, "get_default_install_dir", lambda: tmp_path)

    captured: dict[str, object] = {}

    def fake_run_nuclei_scan(
        binary_path: Path, *, target: str, output_path: Path, **kwargs: object
    ) -> Path:
        captured["binary_path"] = binary_path
        captured["target"] = target
        return output_path

    monkeypatch.setattr(main_module, "run_nuclei_scan", fake_run_nuclei_scan)
    output_path = tmp_path / "out.jsonl"

    result = runner.invoke(
        app, ["scan", "--target", "https://target.example.com", "--output", str(output_path)]
    )

    assert result.exit_code == 0
    assert captured["binary_path"] == binary
    assert captured["target"] == "https://target.example.com"


def test_scan_reports_execution_failure_cleanly(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    binary = tmp_path / "nuclei"
    binary.write_bytes(b"fake")
    monkeypatch.setattr(main_module, "get_default_install_dir", lambda: tmp_path)

    def _boom(*args: object, **kwargs: object) -> Path:
        raise ScanExecutionError("nuclei exited with code 1: fatal error")

    monkeypatch.setattr(main_module, "run_nuclei_scan", _boom)

    result = runner.invoke(
        app,
        ["scan", "--target", "https://target.example.com", "--output", str(tmp_path / "out.jsonl")],
    )

    assert result.exit_code == 1
