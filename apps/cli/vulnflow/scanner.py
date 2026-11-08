"""`vulnflow scan` — PLAN.md FASE 5.4 (local Nuclei binary wrapper).

`runner` is injected (defaulting to `subprocess.run`) so tests never actually
spawn a process or require the real Nuclei binary to be installed — the same
dependency-injection shape used for every other external call in this
project (`httpx.Client` in the API/CLI, `redis.Redis`, Celery's enqueuer).
"""

import subprocess  # nosec: B404
from collections.abc import Callable
from pathlib import Path

_SubprocessRunner = Callable[..., "subprocess.CompletedProcess[bytes]"]


class ScanExecutionError(Exception):
    pass


def run_nuclei_scan(
    binary_path: Path,
    *,
    target: str,
    output_path: Path,
    extra_args: list[str] | None = None,
    runner: _SubprocessRunner = subprocess.run,
) -> Path:
    args = [
        str(binary_path),
        "-target",
        target,
        "-jsonl",
        "-output",
        str(output_path),
        *(extra_args or []),
    ]
    # shell=False (the default) is load-bearing here, not incidental: `target`
    # is attacker-influenceable user input, and shell=True would turn it into
    # a command-injection vector (Bandit B602).
    result = runner(args, shell=False, capture_output=True, check=False)
    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="ignore") if result.stderr else ""
        raise ScanExecutionError(f"nuclei exited with code {result.returncode}: {stderr}")
    return output_path
