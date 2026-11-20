"""Nmap XML parser & normalizer — PLAN.md FASE 5.5 (`defusedxml`, anti-XXE)."""

from pathlib import Path

import pytest
from vulnflow.parsers.nmap_parser import normalize_nmap_finding, parse_nmap_hosts

_SIMPLE_NMAP_XML = """<?xml version="1.0"?>
<nmaprun>
  <host>
    <address addr="10.0.0.5" addrtype="ipv4"/>
    <ports>
      <port protocol="tcp" portid="22">
        <state state="open"/>
        <service name="ssh" product="OpenSSH" version="9.3"/>
      </port>
      <port protocol="tcp" portid="443">
        <state state="open"/>
        <service name="https" product="nginx" version="1.18.0"/>
        <script id="vulners" output="CVE-2021-23017\tCVSS: 9.8"/>
      </port>
      <port protocol="tcp" portid="8080">
        <state state="closed"/>
        <service name="http-proxy"/>
      </port>
    </ports>
  </host>
</nmaprun>
"""

_XXE_NMAP_XML = """<?xml version="1.0"?>
<!DOCTYPE nmaprun [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
<nmaprun>
  <host>
    <address addr="&xxe;" addrtype="ipv4"/>
    <ports/>
  </host>
</nmaprun>
"""


def test_parse_nmap_hosts_only_returns_open_ports(tmp_path: Path) -> None:
    file_path = tmp_path / "scan.xml"
    file_path.write_text(_SIMPLE_NMAP_XML, encoding="utf-8")

    records = list(parse_nmap_hosts(file_path))

    assert len(records) == 2  # the closed 8080 port is excluded
    assert {r["port"] for r in records} == {22, 443}


def test_parse_nmap_hosts_captures_script_output(tmp_path: Path) -> None:
    file_path = tmp_path / "scan.xml"
    file_path.write_text(_SIMPLE_NMAP_XML, encoding="utf-8")

    records = {r["port"]: r for r in parse_nmap_hosts(file_path)}

    assert records[22]["script_output"] is None
    assert "CVE-2021-23017" in (records[443]["script_output"] or "")


def test_parse_nmap_hosts_is_immune_to_xxe(tmp_path: Path) -> None:
    file_path = tmp_path / "evil.xml"
    file_path.write_text(_XXE_NMAP_XML, encoding="utf-8")

    # defusedxml raises on a DOCTYPE with an external/general entity rather
    # than silently resolving it and leaking file contents into `addr`.
    with pytest.raises(Exception):  # noqa: B017 - exact exception type is defusedxml-internal
        list(parse_nmap_hosts(file_path))


def test_normalize_nmap_finding_without_script_is_info_severity() -> None:
    raw = {
        "host": "10.0.0.5",
        "port": 22,
        "protocol": "tcp",
        "service": "ssh",
        "product": "OpenSSH",
        "version": "9.3",
        "script_output": None,
    }

    finding = normalize_nmap_finding(raw)

    assert finding.severity.value == "INFO"
    assert finding.target_host == "10.0.0.5"
    assert finding.target_port == 22
    assert finding.source_tool.value == "nmap"
    assert finding.cwe_id == "UNKNOWN"


def test_normalize_nmap_finding_with_script_output_is_medium_severity() -> None:
    raw = {
        "host": "10.0.0.5",
        "port": 443,
        "protocol": "tcp",
        "service": "https",
        "product": "nginx",
        "version": "1.18.0",
        "script_output": "CVE-2021-23017\tCVSS: 9.8",
    }

    finding = normalize_nmap_finding(raw)

    assert finding.severity.value == "MEDIUM"
    assert "CVE-2021-23017" in finding.proof_of_concept.raw_evidence


def test_parse_nmap_collects_multiple_scripts_and_sctp(tmp_path: Path) -> None:
    xml_data = """<?xml version="1.0"?>
<nmaprun>
  <host>
    <address addr="10.0.0.8" addrtype="ipv4"/>
    <ports>
      <port protocol="sctp" portid="3868">
        <state state="open"/>
        <service name="diameter"/>
        <script id="s1" output="out one"/>
        <script id="s2" output="out two"/>
      </port>
    </ports>
  </host>
</nmaprun>
"""
    xml_file = tmp_path / "multi.xml"
    xml_file.write_text(xml_data, encoding="utf-8")
    records = list(parse_nmap_hosts(xml_file))
    assert len(records) == 1
    assert records[0]["script_output"] is not None
    assert "s1: out one" in records[0]["script_output"]
    assert "s2: out two" in records[0]["script_output"]

    finding = normalize_nmap_finding(dict(records[0]))
    assert finding.protocol.value == "sctp"
    assert finding.severity.value == "MEDIUM"
