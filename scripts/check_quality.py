#!/usr/bin/env python3
"""One-shot quality gate for VulnFlow AI — PLAN.md §2.3 & §4.1.

Runs, in order: Ruff (lint+format) -> Mypy --strict -> Bandit (SAST) ->
Pytest+Coverage -> pip-audit (CVE scan).

Gate scoping (PLAN.md §4.1 "Quality Gate Scoping"):
  - Ruff / Mypy / Bandit / pip-audit are ALWAYS zero-tolerance, from FASE 0
    onward — a single error fails the whole run regardless of phase.
  - Pytest coverage is PROPORTIONAL before FASE 7: missing test directories
    (e.g. tests/test_resilience/ before FASE 7.2 exists) are reported as
    "N/A", not a failure. The hard 85% coverage + 18/18 resilience-test gate
    is only enforced when run with --final (the FASE 7.3 sign-off gate).

Usage:
    uv run python scripts/check_quality.py            # proportional mode (FASE 0-6)
    uv run python scripts/check_quality.py --final     # hard gate (FASE 7.3)
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess  # nosec B404: this script's entire job is shelling out to uv/ruff/mypy/etc.
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _find_uv() -> str | None:
    """Look beyond PATH: pip/pipx installs often land in dirs many shells
    (especially non-interactive Windows sessions) don't load by default."""
    found = shutil.which("uv")
    if found:
        return found

    candidates = [
        Path.home() / ".local" / "bin" / "uv",
        Path.home() / ".local" / "bin" / "uv.exe",
        Path.home() / ".cargo" / "bin" / "uv",
        Path.home() / ".cargo" / "bin" / "uv.exe",
    ]
    appdata = os.environ.get("APPDATA")
    if appdata:
        candidates.extend(Path(appdata).glob("Python/Python3*/Scripts/uv.exe"))

    return next((str(c) for c in candidates if c.is_file()), None)


_found_uv = _find_uv()
if _found_uv is None:
    print(
        "[FATAL] `uv` tidak ditemukan di PATH maupun lokasi instalasi umum.\n"
        "        Install via https://docs.astral.sh/uv/getting-started/installation/\n"
        "        (installer resmi menambahkan uv ke PATH secara otomatis;\n"
        "        `pip install uv` TIDAK cukup di sebagian shell/OS)."
    )
    sys.exit(127)
UV_PATH: str = _found_uv

APP_SOURCE_DIRS = [
    "apps/api/app",
    "apps/cli/vulnflow",
    "packages/contracts/vulnflow_contracts",
]
# scripts/ is self-checked (this file must pass its own gate); tests/ is
# linted by Ruff for style but deliberately excluded from Mypy/Bandit —
# [tool.mypy] exclude and [tool.bandit] exclude_dirs already codify that.
SELF_CHECK_DIRS = ["scripts"]
LINT_ONLY_DIRS = ["tests"]

# Only directories that actually exist are passed to each tool, so a FASE 0
# run (no .py files yet beyond __init__.py stubs) still completes cleanly
# instead of erroring on an empty/placeholder codebase.
EXISTING_SOURCE_DIRS = [d for d in APP_SOURCE_DIRS + SELF_CHECK_DIRS if (ROOT / d).is_dir()]
EXISTING_RUFF_DIRS = [
    d for d in APP_SOURCE_DIRS + SELF_CHECK_DIRS + LINT_ONLY_DIRS if (ROOT / d).is_dir()
]

RESILIENCE_TEST_DIR = ROOT / "tests" / "test_resilience"
REQUIRED_RESILIENCE_TESTS = 18
COVERAGE_HARD_GATE = 85.0
MAX_DETAIL_CHARS = 2000


@dataclass
class StepResult:
    name: str
    passed: bool
    detail: str = ""


def run(cmd: list[str]) -> tuple[int, str]:
    """Run a command via `uv run`, returning (exit_code, combined_output)."""
    # nosec B603/B404: fixed argv list (never shell=True), cmd always built
    # from static lists in this file — never from user/network input.
    proc = subprocess.run(  # nosec
        [UV_PATH, "run", *cmd],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode, (proc.stdout + proc.stderr)


def _run_lint_tool(name: str, dirs: list[str], *commands: list[str]) -> StepResult:
    """Run one or more `uv run <cmd>` invocations against `dirs`.

    Skips entirely (reported as passing) until there's anything to check.
    """
    if not dirs:
        return StepResult(name, True, "(belum ada source dir)")
    outputs = []
    for cmd in commands:
        code, out = run([*cmd, *dirs])
        if code != 0:
            outputs.append(out)
    return StepResult(name, not outputs, "\n".join(outputs)[:MAX_DETAIL_CHARS])


def step_ruff() -> StepResult:
    return _run_lint_tool(
        "Ruff Formatter & Linter",
        EXISTING_RUFF_DIRS,
        ["ruff", "check"],
        ["ruff", "format", "--check"],
    )


def step_mypy() -> StepResult:
    return _run_lint_tool("Mypy Strict Type Check", EXISTING_SOURCE_DIRS, ["mypy", "--strict"])


def step_bandit() -> StepResult:
    return _run_lint_tool("Bandit Security SAST", EXISTING_SOURCE_DIRS, ["bandit", "-q", "-r"])


def _run_pytest_with_coverage() -> tuple[int, str, float | None]:
    coverage_json = ROOT / "coverage.json"
    coverage_json.unlink(missing_ok=True)  # never read a stale report from a prior run
    code, out = run(
        ["pytest", "--cov", "--cov-report=term-missing", "--cov-report=json:coverage.json", "-q"]
    )
    return code, out, _read_coverage_pct()


def _read_coverage_pct() -> float | None:
    coverage_json = ROOT / "coverage.json"
    if not coverage_json.is_file():
        return None
    try:
        data = json.loads(coverage_json.read_text(encoding="utf-8"))
        return float(data["totals"]["percent_covered"])
    except (json.JSONDecodeError, KeyError, ValueError):
        return None


def _count_resilience_tests() -> int:
    if not RESILIENCE_TEST_DIR.is_dir():
        return 0
    return len(list(RESILIENCE_TEST_DIR.glob("test_ec*.py")))


def _evaluate_proportional(
    exit_code: int, pytest_output: str, coverage_pct: float | None
) -> StepResult:
    no_tests_collected = exit_code == 5  # pytest's code for "no tests collected"
    if no_tests_collected:
        return StepResult(
            "Pytest & Evaluasi Coverage", True, "N/A (belum ada modul untuk fase ini)"
        )
    if exit_code != 0:
        return StepResult("Pytest & Evaluasi Coverage", False, pytest_output[:MAX_DETAIL_CHARS])
    detail = (
        f"Coverage: {coverage_pct:.1f}%" if coverage_pct is not None else "(coverage tidak terukur)"
    )
    return StepResult("Pytest & Evaluasi Coverage", True, detail)


def _evaluate_final(exit_code: int, pytest_output: str, coverage_pct: float | None) -> StepResult:
    resilience_count = _count_resilience_tests()
    reasons = []
    if exit_code != 0:
        reasons.append("ada test yang gagal:\n" + pytest_output[:MAX_DETAIL_CHARS])
    if coverage_pct is None or coverage_pct < COVERAGE_HARD_GATE:
        reasons.append(f"coverage {coverage_pct or 0:.1f}% < {COVERAGE_HARD_GATE}%")
    if resilience_count < REQUIRED_RESILIENCE_TESTS:
        reasons.append(
            f"hanya {resilience_count}/{REQUIRED_RESILIENCE_TESTS} test resilience ditemukan"
        )

    passed = not reasons
    detail = f"Coverage: {coverage_pct:.1f}%" if passed else "; ".join(reasons)
    return StepResult("Pytest & Evaluasi Coverage", passed, detail)


def step_pytest(final: bool) -> StepResult:
    exit_code, pytest_output, coverage_pct = _run_pytest_with_coverage()
    if final:
        return _evaluate_final(exit_code, pytest_output, coverage_pct)
    return _evaluate_proportional(exit_code, pytest_output, coverage_pct)


def step_pip_audit() -> StepResult:
    code, out = run(["pip-audit"])
    return StepResult(
        "Kerentanan Dependensi (Audit)", code == 0, "" if code == 0 else out[:MAX_DETAIL_CHARS]
    )


def print_results(steps: list[StepResult]) -> None:
    total = len(steps)
    for i, result in enumerate(steps, start=1):
        mark = "✓ PASS" if result.passed else "✗ FAIL"
        suffix = f" ({result.detail})" if result.detail and result.passed else ""
        print(f"[{i}/{total}] Menjalankan {result.name}...".ljust(55) + f"[{mark}]{suffix}")
        if not result.passed and result.detail:
            print(f"      -> {result.detail}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--final",
        action="store_true",
        help="Tegakkan gerbang akhir FASE 7.3 (85%% coverage + 18/18 test resilience hard-fail).",
    )
    args = parser.parse_args()

    steps = [
        step_ruff(),
        step_mypy(),
        step_bandit(),
        step_pytest(final=args.final),
        step_pip_audit(),
    ]
    print_results(steps)

    all_passed = all(r.passed for r in steps)
    print()
    print(
        "[SUCCESS] Seluruh Quality Gates Lolos! Kode siap di-commit."
        if all_passed
        else "[FAILED] Satu atau lebih Quality Gate gagal. Perbaiki sebelum commit."
    )
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
