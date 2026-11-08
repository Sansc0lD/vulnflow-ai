"""Nmap XML parser & normalizer — PLAN.md FASE 5.5.

Uses `defusedxml` rather than stdlib `xml.etree.ElementTree` (SDD §2.5.4,
EDGE_CASES_AND_RESILIENCE.md §2.2 note): raw Nmap XML comes from a scan
*target* file a CLI user points at, not from this project's own tooling, so
a crafted `<!DOCTYPE>` with an external entity must not be resolved (XXE /
billion-laughs). Open ports carry no CVSS/CWE on their own — Nmap's NSE
vulnerability scripts (`--script vuln`/`vulners`) are the only signal that a
port is more than an informational discovery, so a port with script output
is surfaced as MEDIUM severity and one without is INFO.
"""

from collections.abc import Generator
from pathlib import Path
from typing import Any, TypedDict

from defusedxml import ElementTree

from vulnflow_contracts import (
    ProofOfConceptSchema,
    Protocol,
    Severity,
    SourceTool,
    UnifiedVulnerabilityFinding,
)


class NmapPortRecord(TypedDict):
    host: str
    port: int
    protocol: str
    service: str
    product: str
    version: str
    script_output: str | None


def parse_nmap_hosts(file_path: Path) -> Generator[NmapPortRecord, None, None]:
    tree = ElementTree.parse(str(file_path))
    root = tree.getroot()
    if root is None:
        return

    for host_el in root.findall("host"):
        address_el = host_el.find("address")
        host_addr = address_el.get("addr", "") if address_el is not None else ""

        ports_el = host_el.find("ports")
        if ports_el is None:
            continue

        for port_el in ports_el.findall("port"):
            state_el = port_el.find("state")
            if state_el is None or state_el.get("state") != "open":
                continue

            service_el = port_el.find("service")
            script_el = port_el.find("script")

            yield NmapPortRecord(
                host=host_addr,
                port=int(port_el.get("portid", "0")),
                protocol=port_el.get("protocol", "tcp"),
                service=service_el.get("name", "") if service_el is not None else "",
                product=service_el.get("product", "") if service_el is not None else "",
                version=service_el.get("version", "") if service_el is not None else "",
                script_output=script_el.get("output") if script_el is not None else None,
            )


def normalize_nmap_finding(raw: dict[str, Any]) -> UnifiedVulnerabilityFinding:
    script_output = raw.get("script_output")
    service = raw.get("service") or "unknown"
    port = raw["port"]

    if script_output:
        severity = Severity.MEDIUM
        title = f"Potential vulnerability on port {port}/{service} (Nmap NSE script)"
        reproduction_steps = [
            f"nmap NSE script output on {raw['host']}:{port}/{service}: {script_output}"
        ]
    else:
        severity = Severity.INFO
        title = f"Open port {port}/{service}"
        reproduction_steps = [f"nmap detected an open port at {raw['host']}:{port} ({service})"]

    protocol = Protocol.TCP if raw.get("protocol") == "tcp" else Protocol.UDP

    return UnifiedVulnerabilityFinding(
        title=title,
        severity=severity,
        cvss_score=None,
        cvss_vector=None,
        cwe_id="UNKNOWN",
        target_host=raw["host"],
        target_port=port,
        endpoint_path="",
        protocol=protocol,
        source_tool=SourceTool.NMAP,
        proof_of_concept=ProofOfConceptSchema(
            raw_evidence=str(raw),
            reproduction_steps=reproduction_steps,
        ),
    )
