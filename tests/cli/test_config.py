"""CLI local config persistence — PLAN.md FASE 5.2 (EC-01)."""

from pathlib import Path

import pytest
from vulnflow.config import CLIConfig, ConfigNotFoundError, load_config, save_config


def test_save_then_load_round_trips_fields(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    config = CLIConfig(
        api_url="https://api.vulnflow.ai",
        api_key="vf_live_abc123",
        active_workspace_id="11111111-1111-1111-1111-111111111111",
    )

    save_config(config, path=config_path)
    loaded = load_config(path=config_path)

    assert loaded == config


def test_save_config_creates_parent_directories(tmp_path: Path) -> None:
    config_path = tmp_path / "nested" / ".vulnflow" / "config.json"
    config = CLIConfig(
        api_url="https://api.vulnflow.ai",
        api_key="vf_live_abc123",
        active_workspace_id="11111111-1111-1111-1111-111111111111",
    )

    save_config(config, path=config_path)

    assert config_path.exists()


def test_load_config_raises_when_missing(tmp_path: Path) -> None:
    missing_path = tmp_path / "does-not-exist.json"

    with pytest.raises(ConfigNotFoundError):
        load_config(path=missing_path)


def test_load_config_raises_clear_error_on_corrupt_json(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text("{ not valid json", encoding="utf-8")

    with pytest.raises(ConfigNotFoundError):
        load_config(path=config_path)
