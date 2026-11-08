"""`vulnflow setup-tools` — PLAN.md FASE 5.3 (cross-platform Nuclei provisioning).

GitHub's real release asset names embed the version number
(`nuclei_3.11.1_linux_amd64.zip`), not just the OS/arch
(`nuclei_linux_amd64.zip`) — confirmed by actually running `setup-tools`
against the live GitHub API during manual testing, where the naive
`/releases/latest/download/nuclei_{os}_{arch}.zip` URL 404'd. `/releases/latest/download/<name>`
only redirects for an *exact* existing asset name, so the version has to be
resolved first via the releases API, then used to build the real filename.
"""

import io
import stat
import zipfile
from collections.abc import Callable
from pathlib import Path

import httpx
import pytest
from vulnflow.environment import TargetEnvironment
from vulnflow.tool_provisioner import ToolProvisioningError, ensure_tools_installed

_LATEST_RELEASE_API_URL = "https://api.github.com/repos/projectdiscovery/nuclei/releases/latest"


def _zip_bytes(members: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        for name, content in members.items():
            zf.writestr(name, content)
    return buffer.getvalue()


def _linux_env() -> TargetEnvironment:
    return TargetEnvironment(
        os_tag="linux", arch_tag="amd64", extension=".zip", binary_name="nuclei"
    )


def _two_step_handler(
    archive: bytes, *, version: str = "3.11.1", download_status: int = 200
) -> Callable[[httpx.Request], httpx.Response]:
    """Simulates the real two-request flow: resolve the latest version via
    the GitHub releases API, then download that exact versioned asset."""

    def handler(request: httpx.Request) -> httpx.Response:
        if str(request.url) == _LATEST_RELEASE_API_URL:
            return httpx.Response(200, json={"tag_name": f"v{version}"})
        return httpx.Response(download_status, content=archive)

    return handler


def test_downloads_real_versioned_asset_name_not_the_unversioned_guess(tmp_path: Path) -> None:
    # Regression test for the exact bug found in manual testing: the
    # download URL must include the resolved version, matching GitHub's
    # real asset naming, not the version-less filename the old code guessed.
    archive = _zip_bytes({"nuclei": b"fake-nuclei"})
    requested_urls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested_urls.append(str(request.url))
        return _two_step_handler(archive, version="3.11.1")(request)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    install_dir = tmp_path / "bin"

    ensure_tools_installed(install_dir, client=client, env=_linux_env())

    assert requested_urls[0] == _LATEST_RELEASE_API_URL
    assert requested_urls[1] == (
        "https://github.com/projectdiscovery/nuclei/releases/download/"
        "v3.11.1/nuclei_3.11.1_linux_amd64.zip"
    )


def test_downloads_and_extracts_binary_when_absent(tmp_path: Path) -> None:
    archive = _zip_bytes({"nuclei": b"#!/bin/sh\necho fake-nuclei"})
    client = httpx.Client(transport=httpx.MockTransport(_two_step_handler(archive)))
    install_dir = tmp_path / "bin"

    result = ensure_tools_installed(install_dir, client=client, env=_linux_env())

    assert result == install_dir / "nuclei"
    assert result.read_bytes() == b"#!/bin/sh\necho fake-nuclei"


def test_sets_executable_bit_on_non_windows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # `Path.chmod` on Windows doesn't actually toggle a Unix exec bit (the
    # filesystem has no such concept), so asserting real `stat()` output
    # after the call would be testing Windows' chmod semantics, not ours.
    # Spying on the call itself is what's actually under test here.
    chmod_calls: list[int] = []
    original_chmod = Path.chmod

    def _spy_chmod(self: Path, mode: int) -> None:
        chmod_calls.append(mode)
        original_chmod(self, mode)

    monkeypatch.setattr(Path, "chmod", _spy_chmod)

    archive = _zip_bytes({"nuclei": b"binary-content"})
    client = httpx.Client(transport=httpx.MockTransport(_two_step_handler(archive)))
    install_dir = tmp_path / "bin"

    ensure_tools_installed(install_dir, client=client, env=_linux_env())

    assert len(chmod_calls) == 1
    assert chmod_calls[0] & stat.S_IEXEC


def test_skips_download_when_binary_already_exists(tmp_path: Path) -> None:
    install_dir = tmp_path / "bin"
    install_dir.mkdir(parents=True)
    existing = install_dir / "nuclei"
    existing.write_bytes(b"already-here")

    def handler(_: httpx.Request) -> httpx.Response:
        raise AssertionError("must not make a network call when the binary already exists")

    client = httpx.Client(transport=httpx.MockTransport(handler))

    result = ensure_tools_installed(install_dir, client=client, env=_linux_env())

    assert result == existing
    assert result.read_bytes() == b"already-here"


def test_raises_when_archive_missing_expected_binary(tmp_path: Path) -> None:
    archive = _zip_bytes({"README.txt": b"not a binary"})
    client = httpx.Client(transport=httpx.MockTransport(_two_step_handler(archive)))
    install_dir = tmp_path / "bin"

    with pytest.raises(ToolProvisioningError):
        ensure_tools_installed(install_dir, client=client, env=_linux_env())


def test_raises_on_download_http_error(tmp_path: Path) -> None:
    client = httpx.Client(
        transport=httpx.MockTransport(_two_step_handler(b"", download_status=404))
    )
    install_dir = tmp_path / "bin"

    with pytest.raises(httpx.HTTPStatusError):
        ensure_tools_installed(install_dir, client=client, env=_linux_env())


def test_raises_on_version_resolution_http_error(tmp_path: Path) -> None:
    client = httpx.Client(
        transport=httpx.MockTransport(lambda req: httpx.Response(503, content=b"unavailable"))
    )
    install_dir = tmp_path / "bin"

    with pytest.raises(httpx.HTTPStatusError):
        ensure_tools_installed(install_dir, client=client, env=_linux_env())
