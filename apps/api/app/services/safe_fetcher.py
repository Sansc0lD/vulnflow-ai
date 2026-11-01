"""SafeURLFetcher — anti-SSRF guard + fetcher for WeasyPrint image/resource loads.

SDD §2.5.4. Hardened versus SDD §2.5.4's own reference snippet (flagged in
the FASE-2 audit): uses `ipaddress` properties instead of a manual CIDR
allowlist, so it also blocks reserved/unspecified/multicast ranges and
IPv4-mapped IPv6 addresses (e.g. ``::ffff:127.0.0.1``).

FASE 4.7 revision — closes a DNS-rebinding gap found after FASE 3 (see
PROJECT_CONTEXT.md risk #11): the earlier design validated a resolved IP
then delegated to an opaque `default_fetcher`, which re-resolved DNS
independently when it actually connected — a different DNS answer on the
second lookup bypassed the guard entirely. This version performs the fetch
itself, connecting directly to the validated IP (one resolution, ever)
while still sending the original hostname as the `Host` header and TLS SNI
extension, so a legitimate virtual-hosted/TLS target still works correctly.
"""

import base64
import ipaddress
import socket
import urllib.parse
from typing import Any

import httpx

_ALLOWED_SCHEMES = {"http", "https"}
_DEFAULT_TIMEOUT_SECONDS = 10.0
# F4-MED-19: Explicitly block CGNAT range 100.64.0.0/10 (RFC 6598)
_CGNAT_NETWORK = ipaddress.ip_network("100.64.0.0/10")


class SSRFBlockedError(PermissionError):
    pass


def _resolve_ip(hostname: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address:
    try:
        return ipaddress.ip_address(hostname)
    except ValueError:
        pass
    try:
        resolved = socket.gethostbyname(hostname)
    except OSError as exc:
        raise SSRFBlockedError(f"Could not resolve hostname: {hostname!r}") from exc
    return ipaddress.ip_address(resolved)


def _is_blocked_address(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
        ip = ip.ipv4_mapped
    if ip in _CGNAT_NETWORK:
        return True
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_unspecified
        or ip.is_multicast
    )


def _pinned_netloc(ip: ipaddress.IPv4Address | ipaddress.IPv6Address, port: int | None) -> str:
    host = f"[{ip}]" if isinstance(ip, ipaddress.IPv6Address) else str(ip)
    return f"{host}:{port}" if port else host


def _fetch_data_uri(url: str) -> dict[str, Any]:
    header, _, encoded = url.removeprefix("data:").partition(",")
    mime_type = header.split(";")[0] or "text/plain"
    is_base64 = ";base64" in header
    content = base64.b64decode(encoded) if is_base64 else urllib.parse.unquote_to_bytes(encoded)
    return {"string": content, "mime_type": mime_type}


def safe_url_fetcher(
    url: str, *, client: httpx.Client | None = None, timeout: float = _DEFAULT_TIMEOUT_SECONDS
) -> dict[str, Any]:
    # F4-LOW-16: catch ValueError when URL parsing or port is out of range
    try:
        parsed = urllib.parse.urlsplit(url)
        _ = parsed.port
    except ValueError as exc:
        raise SSRFBlockedError(f"Invalid URL or port number: {exc}") from exc

    if parsed.scheme == "data":
        return _fetch_data_uri(url)
    if parsed.scheme not in _ALLOWED_SCHEMES:
        raise SSRFBlockedError(f"Blocked URI scheme: {parsed.scheme!r}")
    if not parsed.hostname:
        raise SSRFBlockedError("URL has no hostname")

    ip = _resolve_ip(parsed.hostname)
    if _is_blocked_address(ip):
        raise SSRFBlockedError(f"Blocked private/reserved address: {ip}")

    pinned_url = urllib.parse.urlunsplit(
        (
            parsed.scheme,
            _pinned_netloc(ip, parsed.port),
            parsed.path or "/",
            parsed.query,
            parsed.fragment,
        )
    )

    owns_client = client is None
    client = client or httpx.Client(timeout=timeout)
    try:
        # F4-MED-20: explicitly set follow_redirects=False to prevent redirect-based SSRF
        response = client.get(
            pinned_url,
            headers={"Host": parsed.hostname},
            extensions={"sni_hostname": parsed.hostname},
            follow_redirects=False,
        )
    finally:
        if owns_client:
            client.close()

    response.raise_for_status()
    return {
        "string": response.content,
        "mime_type": response.headers.get("content-type", "application/octet-stream"),
    }
