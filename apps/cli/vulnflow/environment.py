"""OS/CPU detection for cross-platform Nuclei provisioning — PLAN.md FASE 5.3.

EDGE_CASES_AND_RESILIENCE.md §2.2. `system`/`machine` are accepted as
parameters (defaulting to the real `platform` module) so every OS/arch branch
is testable on a single CI machine without mocking `platform` globally.

Deliberately does NOT build a download URL here (unlike an earlier version of
this module, and unlike EDGE_CASES_AND_RESILIENCE.md §2.2's own reference
snippet): confirmed by actually running `setup-tools` against the live
GitHub API, Nuclei's real release assets are named `nuclei_<version>_<os>_
<arch>.zip` — the version is embedded in the filename, so no URL can be
built from OS/arch alone. `tool_provisioner.py` resolves the version first.
"""

import platform
from dataclasses import dataclass


@dataclass(frozen=True)
class TargetEnvironment:
    os_tag: str
    arch_tag: str
    extension: str
    binary_name: str


def resolve_target_environment(
    *, system: str | None = None, machine: str | None = None
) -> TargetEnvironment:
    os_raw = (system if system is not None else platform.system()).lower()
    arch_raw = (machine if machine is not None else platform.machine()).lower()

    if "windows" in os_raw:
        os_tag, extension, binary_name = "windows", ".zip", "nuclei.exe"
    elif "darwin" in os_raw:
        os_tag, extension, binary_name = "macOS", ".zip", "nuclei"
    else:
        os_tag, extension, binary_name = "linux", ".zip", "nuclei"

    if arch_raw in {"amd64", "x86_64"}:
        arch_tag = "amd64"
    elif arch_raw in {"arm64", "aarch64"}:
        arch_tag = "arm64"
    else:
        arch_tag = "386"

    return TargetEnvironment(
        os_tag=os_tag,
        arch_tag=arch_tag,
        extension=extension,
        binary_name=binary_name,
    )
