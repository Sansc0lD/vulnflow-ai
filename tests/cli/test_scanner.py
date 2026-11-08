"""`vulnflow scan` — PLAN.md FASE 5.4 (local Nuclei binary wrapper)."""

import subprocess
from pathlib import Path

import pytest
from vulnflow.scanner import ScanExecutionError, run_nuclei_scan


def test_run_nuclei_scan_invokes_binary_with_expected_args(tmp_path: Path) -> None:
    captured_args: list[str] = []

    def fake_runner(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        captured_args.extend(args)
        return subprocess.CompletedProcess(args, returncode=0, stdout=b"", stderr=b"")

    binary = tmp_path / "nuclei"
    output_path = tmp_path / "out.jsonl"

    result = run_nuclei_scan(
        binary, target="https://target.example.com", output_path=output_path, runner=fake_runner
    )

    assert result == output_path
    assert captured_args[0] == str(binary)
    assert "https://target.example.com" in captured_args
    assert str(output_path) in captured_args


def test_run_nuclei_scan_never_uses_a_shell(tmp_path: Path) -> None:
    captured_kwargs: dict[str, object] = {}

    def fake_runner(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        captured_kwargs.update(kwargs)
        return subprocess.CompletedProcess(args, returncode=0, stdout=b"", stderr=b"")

    run_nuclei_scan(
        tmp_path / "nuclei",
        target="https://target.example.com",
        output_path=tmp_path / "out.jsonl",
        runner=fake_runner,
    )

    assert captured_kwargs.get("shell", False) is False


def test_run_nuclei_scan_raises_on_nonzero_exit(tmp_path: Path) -> None:
    def failing_runner(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        return subprocess.CompletedProcess(args, returncode=1, stdout=b"", stderr=b"fatal error")

    with pytest.raises(ScanExecutionError):
        run_nuclei_scan(
            tmp_path / "nuclei",
            target="https://target.example.com",
            output_path=tmp_path / "out.jsonl",
            runner=failing_runner,
        )
