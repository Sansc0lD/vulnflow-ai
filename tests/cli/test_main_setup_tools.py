"""`vulnflow setup-tools` command wiring — PLAN.md FASE 5.3."""

from pathlib import Path

import pytest
import vulnflow.main as main_module
from typer.testing import CliRunner
from vulnflow.environment import TargetEnvironment
from vulnflow.main import app
from vulnflow.tool_provisioner import ToolProvisioningError

runner = CliRunner()


def test_setup_tools_reports_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    install_dir = tmp_path / "bin"
    monkeypatch.setattr(main_module, "get_default_install_dir", lambda: install_dir)
    monkeypatch.setattr(
        main_module,
        "ensure_tools_installed",
        lambda _install_dir, *, client, env=None: install_dir / "nuclei",
    )

    result = runner.invoke(app, ["setup-tools"])

    assert result.exit_code == 0
    assert "nuclei" in result.stdout.lower()


def test_setup_tools_reports_failure_cleanly(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _boom(_install_dir: Path, *, client: object, env: TargetEnvironment | None = None) -> Path:
        raise ToolProvisioningError("archive missing expected binary")

    monkeypatch.setattr(main_module, "get_default_install_dir", lambda: tmp_path / "bin")
    monkeypatch.setattr(main_module, "ensure_tools_installed", _boom)

    result = runner.invoke(app, ["setup-tools"])

    assert result.exit_code == 1
    combined_output = result.stdout + (result.stderr if result.stderr_bytes is not None else "")
    assert "archive missing expected binary" in combined_output
