"""`vulnflow setup-tools` — PLAN.md FASE 5.3.

EDGE_CASES_AND_RESILIENCE.md §2.2 flags its own reference snippet as unsafe
for direct reuse: `urllib.request.urlretrieve` trips Bandit B310 (unverified
URL scheme) and blind `zip_ref.extract(member, dir)` over an attacker-served
archive is a path-traversal risk (B202) if that member name is ever anything
other than a name we chose ourselves. This version downloads via the
already-audited `httpx` client (consistent with every other outbound call in
this codebase) and only ever asks the archive for one exact, hardcoded member
name — `env.binary_name`, never a name read out of the archive itself — so
there is no attacker-controlled path component to resolve in the first place.

Version resolution: confirmed by actually running `setup-tools` against the
live GitHub API (manual testing caught this, no unit test would have), real
Nuclei release assets are named `nuclei_<version>_<os>_<arch>.zip` — the
version is embedded in the filename. `/releases/latest/download/<name>` only
redirects for an asset name that exists verbatim, so the version has to be
resolved via the releases API first, then used to build the real filename.
"""

import stat
import zipfile
from pathlib import Path

import httpx

from vulnflow.environment import TargetEnvironment, resolve_target_environment

_LATEST_RELEASE_API_URL = "https://api.github.com/repos/projectdiscovery/nuclei/releases/latest"
_RELEASE_DOWNLOAD_BASE = "https://github.com/projectdiscovery/nuclei/releases/download"


class ToolProvisioningError(Exception):
    pass


def resolve_latest_nuclei_version(client: httpx.Client) -> str:
    response = client.get(_LATEST_RELEASE_API_URL)
    response.raise_for_status()
    tag_name: str = response.json()["tag_name"]
    return tag_name.removeprefix("v")


def build_download_url(env: TargetEnvironment, version: str) -> str:
    return (
        f"{_RELEASE_DOWNLOAD_BASE}/v{version}/"
        f"nuclei_{version}_{env.os_tag}_{env.arch_tag}{env.extension}"
    )


def _extract_expected_binary(archive_path: Path, member_name: str, dest_dir: Path) -> None:
    with zipfile.ZipFile(archive_path) as zip_ref:
        try:
            info = zip_ref.getinfo(member_name)
        except KeyError as exc:
            raise ToolProvisioningError(
                f"Downloaded archive does not contain the expected binary '{member_name}'."
            ) from exc

        destination = (dest_dir / member_name).resolve()
        if dest_dir.resolve() not in destination.parents and destination != dest_dir.resolve():
            # Unreachable while member_name is one of our own hardcoded
            # constants (never read from the archive), kept as an explicit,
            # tested guard rather than relying on that invariant silently.
            raise ToolProvisioningError(f"Refusing to extract unsafe path: {member_name!r}")

        zip_ref.extract(info, dest_dir)


def ensure_tools_installed(
    install_dir: Path,
    *,
    client: httpx.Client,
    env: TargetEnvironment | None = None,
) -> Path:
    env = env or resolve_target_environment()
    install_dir.mkdir(parents=True, exist_ok=True)
    target_binary = install_dir / env.binary_name
    if target_binary.exists():
        return target_binary

    version = resolve_latest_nuclei_version(client)
    response = client.get(build_download_url(env, version))
    response.raise_for_status()

    archive_path = install_dir / f"nuclei_temp{env.extension}"
    archive_path.write_bytes(response.content)
    try:
        _extract_expected_binary(archive_path, env.binary_name, install_dir)
    finally:
        archive_path.unlink(missing_ok=True)

    if env.os_tag != "windows":
        current_mode = target_binary.stat().st_mode
        target_binary.chmod(current_mode | stat.S_IEXEC)

    return target_binary
