"""`vulnflow configure` subcommand — PLAN.md FASE 5.1/5.2 (EC-01)."""

from pathlib import Path

import pytest
from typer.testing import CliRunner
from vulnflow.config import load_config
from vulnflow.main import app

runner = CliRunner()


@pytest.fixture(autouse=True)
def _isolated_config_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    config_path = tmp_path / "config.json"
    monkeypatch.setattr("vulnflow.config.get_config_path", lambda: config_path)
    return config_path


def test_configure_saves_token_and_workspace(_isolated_config_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "configure",
            "--token",
            "vf_live_abc123",
            "--workspace",
            "11111111-1111-1111-1111-111111111111",
            "--api-url",
            "https://api.vulnflow.ai",
        ],
    )

    assert result.exit_code == 0
    assert "Configuration saved" in result.stdout

    saved = load_config(path=_isolated_config_path)
    assert saved.api_key == "vf_live_abc123"
    assert saved.active_workspace_id == "11111111-1111-1111-1111-111111111111"
    assert saved.api_url == "https://api.vulnflow.ai"


def test_configure_defaults_api_url_to_localhost(_isolated_config_path: Path) -> None:
    result = runner.invoke(
        app,
        ["configure", "--token", "vf_live_abc123", "--workspace", "wsp-01"],
    )

    assert result.exit_code == 0
    saved = load_config(path=_isolated_config_path)
    assert saved.api_url == "http://localhost:8000"


def test_configure_rejects_empty_token(_isolated_config_path: Path) -> None:
    result = runner.invoke(app, ["configure", "--token", "", "--workspace", "wsp-01"])

    assert result.exit_code != 0
