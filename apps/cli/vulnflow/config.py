"""CLI local config persistence — PLAN.md FASE 5.2 (EC-01).

`active_workspace_id` is what makes EC-01 enforceable client-side: a pentester
who belongs to multiple workspaces always pushes against one explicit,
locally-stored workspace rather than whatever the API happens to default to.
"""

import json
import os
from pathlib import Path

from pydantic import BaseModel, ConfigDict, ValidationError


class CLIConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    api_url: str
    api_key: str
    active_workspace_id: str


class ConfigNotFoundError(Exception):
    """Raised when no usable config exists yet — the user must run `vulnflow configure`."""


def get_config_path() -> Path:
    return Path.home() / ".vulnflow" / "config.json"


def normalize_api_url(api_url: str) -> str:
    cleaned = api_url.strip().rstrip("/")
    for suffix in ("/api/v1", "/api"):
        if cleaned.endswith(suffix):
            cleaned = cleaned[: -len(suffix)].rstrip("/")
            break
    return cleaned


def save_config(config: CLIConfig, *, path: Path | None = None) -> Path:
    target = path or get_config_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    data = config.model_dump_json(indent=2).encode("utf-8")
    # api_key is a bearer secret. Writing via `Path.write_text()` then
    # `chmod(0o600)` afterward leaves a window where the file sits at
    # default (umask) permissions before being restricted — a local
    # multi-user race. `os.open` with the mode set at O_CREAT time applies
    # the restriction atomically on Linux/macOS, where this CLI is actually
    # expected to run per SDD §4.1 (a no-op on Windows either way, same as
    # before). The trailing chmod is kept to self-heal a pre-existing file
    # from an older version of this CLI that didn't restrict permissions.
    fd = os.open(target, os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o600)
    try:
        os.write(fd, data)
    finally:
        os.close(fd)
    target.chmod(0o600)
    return target


def load_config(*, path: Path | None = None) -> CLIConfig:
    target = path or get_config_path()
    if not target.exists():
        raise ConfigNotFoundError(
            f"No configuration found at {target}. Run `vulnflow configure` first."
        )
    try:
        return CLIConfig.model_validate_json(target.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, ValidationError) as exc:
        raise ConfigNotFoundError(
            f"Configuration at {target} is corrupt or invalid: {exc}. "
            "Run `vulnflow configure` again."
        ) from exc
