"""OS/CPU detection for cross-platform tool provisioning — PLAN.md FASE 5.3."""

import pytest
from vulnflow.environment import resolve_target_environment


@pytest.mark.parametrize(
    ("system", "machine", "expected_os", "expected_binary"),
    [
        ("Windows", "AMD64", "windows", "nuclei.exe"),
        ("Darwin", "x86_64", "macOS", "nuclei"),
        ("Darwin", "arm64", "macOS", "nuclei"),
        ("Linux", "x86_64", "linux", "nuclei"),
    ],
)
def test_resolve_target_environment_normalizes_os(
    system: str, machine: str, expected_os: str, expected_binary: str
) -> None:
    env = resolve_target_environment(system=system, machine=machine)

    assert env.os_tag == expected_os
    assert env.binary_name == expected_binary


@pytest.mark.parametrize(
    ("machine", "expected_arch"),
    [
        ("AMD64", "amd64"),
        ("x86_64", "amd64"),
        ("arm64", "arm64"),
        ("aarch64", "arm64"),
        ("i686", "386"),
    ],
)
def test_resolve_target_environment_normalizes_arch(machine: str, expected_arch: str) -> None:
    env = resolve_target_environment(system="Linux", machine=machine)

    assert env.arch_tag == expected_arch
