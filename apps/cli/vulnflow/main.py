"""CLI entrypoint — PLAN.md FASE 5.1 (`Typer` + `Rich`, SDD §4.1)."""

from pathlib import Path

import httpx
import typer
from pydantic import ValidationError

from vulnflow import __version__
from vulnflow.config import CLIConfig, ConfigNotFoundError, load_config, save_config
from vulnflow.environment import resolve_target_environment
from vulnflow.ingest_client import (
    FreeTierBatchLimitError,
    IngestClientError,
    IngestTransientError,
    chunk_findings,
    compute_file_hash,
    compute_idempotency_key,
    push_batch,
)
from vulnflow.parsers.nmap_parser import normalize_nmap_finding, parse_nmap_hosts
from vulnflow.parsers.nuclei_parser import normalize_nuclei_finding, parse_nuclei_stream
from vulnflow.scanner import ScanExecutionError, run_nuclei_scan
from vulnflow.tool_provisioner import ToolProvisioningError, ensure_tools_installed
from vulnflow_contracts import ScanMetadata, UnifiedVulnerabilityFinding

DEFAULT_API_URL = "http://localhost:8000"
FREE_TIER_TOP_N = 50
_SEVERITY_RANK = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}


def get_default_install_dir() -> Path:
    return Path.home() / ".vulnflow" / "bin"


app = typer.Typer(
    name="vulnflow",
    help="VulnFlow AI Local CLI Agent — scan ingestion & reporting assistant.",
    no_args_is_help=True,
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"vulnflow-cli {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Print the installed vulnflow-cli version and exit.",
    ),
) -> None:
    """VulnFlow AI Local CLI Agent."""


@app.command()
def configure(
    token: str = typer.Option(..., "--token", help="API key issued by a workspace MANAGER."),
    workspace: str = typer.Option(..., "--workspace", help="Active workspace id (EC-01)."),
    api_url: str = typer.Option(DEFAULT_API_URL, "--api-url", help="VulnFlow AI API base URL."),
) -> None:
    """Save API credentials and the active workspace locally (SDD §4.1.1, EC-01)."""
    if not token.strip():
        typer.echo("[-] --token must not be empty.", err=True)
        raise typer.Exit(code=1)
    if not workspace.strip():
        typer.echo("[-] --workspace must not be empty.", err=True)
        raise typer.Exit(code=1)

    config = CLIConfig(api_url=api_url.rstrip("/"), api_key=token, active_workspace_id=workspace)
    path = save_config(config)
    typer.echo(f"[+] Configuration saved to {path}")


@app.command(name="setup-tools")
def setup_tools() -> None:
    """Download the Nuclei scanner binary for this OS/CPU (SDD §2.2.2, EDGE_CASES §2)."""
    env = resolve_target_environment()
    typer.echo(f"[*] Detected platform: {env.os_tag}/{env.arch_tag}")
    install_dir = get_default_install_dir()
    try:
        with httpx.Client(timeout=60.0, follow_redirects=True) as client:
            binary_path = ensure_tools_installed(install_dir, client=client, env=env)
    except (httpx.HTTPError, ToolProvisioningError) as exc:
        typer.echo(f"[-] Failed to install Nuclei: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"[+] Nuclei ready at {binary_path}")


@app.command()
def scan(
    target: str = typer.Option(..., "--target", help="Target URL or host to scan."),
    output: Path = typer.Option(..., "--output", help="Where to write Nuclei's JSONL output."),
    nuclei_path: Path | None = typer.Option(
        None, "--nuclei-path", help="Path to the nuclei binary (default: ~/.vulnflow/bin)."
    ),
) -> None:
    """Run a local Nuclei scan against a target (SDD §2.2.2, PLAN.md FASE 5.4)."""
    binary_path = nuclei_path or (
        get_default_install_dir() / resolve_target_environment().binary_name
    )
    if not binary_path.exists():
        typer.echo(
            f"[-] Nuclei binary not found at {binary_path}. Run `vulnflow setup-tools` first.",
            err=True,
        )
        raise typer.Exit(code=1)

    typer.echo(f"[*] Scanning {target} with {binary_path} ...")
    try:
        run_nuclei_scan(binary_path, target=target, output_path=output)
    except ScanExecutionError as exc:
        typer.echo(f"[-] Scan failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"[+] Scan complete. Output written to {output}")


def _normalize_findings(
    scan_type: str, file: Path
) -> tuple[list[UnifiedVulnerabilityFinding], int]:
    findings: list[UnifiedVulnerabilityFinding] = []
    skipped = 0

    if scan_type == "nuclei":
        for raw in parse_nuclei_stream(file):
            try:
                findings.append(normalize_nuclei_finding(raw))
            except ValidationError:
                skipped += 1
    elif scan_type == "nmap":
        for nmap_raw in parse_nmap_hosts(file):
            try:
                findings.append(normalize_nmap_finding(dict(nmap_raw)))
            except ValidationError:
                skipped += 1
    else:
        raise typer.BadParameter(f"Unsupported --type '{scan_type}'. Use 'nuclei' or 'nmap'.")

    return findings, skipped


@app.command()
def push(
    project: str = typer.Option(..., "--project", help="Target project id."),
    type: str = typer.Option(..., "--type", help="Scanner output type: 'nuclei' or 'nmap'."),
    file: Path = typer.Option(
        ..., "--file", exists=True, readable=True, help="Path to the scan output file."
    ),
) -> None:
    """Parse a scan output file and ingest it into a project (SDD §4.1.1, EC-06/EC-07/EC-10)."""
    try:
        config = load_config()
    except ConfigNotFoundError as exc:
        typer.echo(f"[-] {exc}", err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(f"[*] Parsing {file} ...")
    findings, skipped = _normalize_findings(type, file)
    if skipped:
        typer.echo(f"[!] Skipped {skipped} malformed finding(s).")
    if not findings:
        typer.echo("[-] No valid findings to push.", err=True)
        raise typer.Exit(code=1)
    typer.echo(f"    -> Found {len(findings)} findings")

    scan_metadata = ScanMetadata(
        scanner_name=type, scanner_version="unknown", scan_duration_seconds=0.0
    )
    file_hash = compute_file_hash(file)
    chunks = chunk_findings(findings)

    new_total = duplicate_total = quarantined_total = 0
    with httpx.Client(timeout=30.0) as client:
        for index, chunk in enumerate(chunks):
            chunk_index = index if len(chunks) > 1 else None
            idempotency_key = compute_idempotency_key(file_hash, chunk_index)
            try:
                result = push_batch(
                    client,
                    api_url=config.api_url,
                    workspace_id=config.active_workspace_id,
                    project_id=project,
                    api_key=config.api_key,
                    findings=chunk,
                    scan_metadata=scan_metadata,
                    idempotency_key=idempotency_key,
                )
            except FreeTierBatchLimitError as exc:
                typer.echo(f"[!] {exc}")
                if not typer.confirm(
                    f"Upload only the top {FREE_TIER_TOP_N} highest-severity findings instead?"
                ):
                    typer.echo("[-] Upload cancelled.", err=True)
                    raise typer.Exit(code=1) from exc
                top_n = sorted(chunk, key=lambda f: _SEVERITY_RANK.get(f.severity.value, 99))[
                    :FREE_TIER_TOP_N
                ]
                result = push_batch(
                    client,
                    api_url=config.api_url,
                    workspace_id=config.active_workspace_id,
                    project_id=project,
                    api_key=config.api_key,
                    findings=top_n,
                    scan_metadata=scan_metadata,
                    idempotency_key=f"{idempotency_key}:top{FREE_TIER_TOP_N}",
                )
            except (IngestTransientError, IngestClientError) as exc:
                typer.echo(f"[-] Upload failed: {exc}", err=True)
                raise typer.Exit(code=1) from exc

            new_total += result.new_findings_count
            duplicate_total += result.duplicate_findings_count
            quarantined_total += result.quarantined_count

    typer.echo(
        f"[+] SUCCESS: {new_total} new, {duplicate_total} duplicated, "
        f"{quarantined_total} quarantined"
    )


if __name__ == "__main__":
    app()
