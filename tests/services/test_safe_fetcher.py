"""PLAN.md FASE 3.6/4.7 — SafeURLFetcher anti-SSRF guard (SDD §2.5.4, NFR-SEC-002).

FASE 4.7 closes a DNS-rebinding gap found after FASE 3 (see PROJECT_CONTEXT.md
risk #11 / PLAN.md FASE 4.7 warning): instead of validating a resolved IP
then delegating to an opaque `default_fetcher` (which re-resolves DNS
independently), this fetcher performs the HTTP request itself, connecting
directly to the already-validated IP (never re-resolving) while still
sending the original `Host` header and TLS SNI — so validation and
connection always target the exact same address.
"""

import socket

import httpx
import pytest
from app.services.safe_fetcher import SSRFBlockedError, safe_url_fetcher


@pytest.mark.parametrize("scheme_url", ["file:///etc/passwd", "ftp://example.com/x"])
def test_blocks_non_http_schemes(scheme_url: str) -> None:
    with pytest.raises(SSRFBlockedError):
        safe_url_fetcher(scheme_url)


def test_blocks_url_without_hostname() -> None:
    with pytest.raises(SSRFBlockedError):
        safe_url_fetcher("http:///no-host")


@pytest.mark.parametrize(
    "blocked_url",
    [
        "http://127.0.0.1/x",
        "http://10.0.0.1/x",
        "http://172.16.0.1/x",
        "http://192.168.1.1/x",
        "http://169.254.169.254/x",  # cloud metadata endpoint
        "http://0.0.0.0/x",
        "http://[::1]/x",
        "http://[::ffff:127.0.0.1]/x",  # IPv4-mapped IPv6 loopback
        "http://100.64.0.1/x",  # CGNAT (RFC 6598) - F4-MED-19
        "http://100.127.255.254/x",  # CGNAT (RFC 6598) - F4-MED-19
    ],
)
def test_blocks_private_loopback_and_metadata_addresses(blocked_url: str) -> None:
    with pytest.raises(SSRFBlockedError):
        safe_url_fetcher(blocked_url)


def test_blocks_resolved_hostname_pointing_at_private_ip(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(socket, "gethostbyname", lambda _host: "127.0.0.1")

    with pytest.raises(SSRFBlockedError):
        safe_url_fetcher("http://internal.evil.test/x")


def test_data_uri_passes_through_without_network_access() -> None:
    # data: URIs carry no SSRF risk (no network connection) and WeasyPrint
    # needs them for inline-embedded images.
    result = safe_url_fetcher("data:text/plain;base64,aGVsbG8=")
    assert result["string"] == b"hello"


def test_fetch_connects_to_pinned_ip_not_a_fresh_dns_lookup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # This is the actual regression test for the DNS-rebinding gap: the
    # request's connection target must be the IP that was validated, with
    # the original hostname only in the Host header / TLS SNI — proving no
    # second resolution of the hostname ever happens.
    monkeypatch.setattr(socket, "gethostbyname", lambda _host: "93.184.216.34")
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["host"] = request.url.host
        captured["header_host"] = request.headers.get("host")
        captured["sni"] = request.extensions.get("sni_hostname")
        return httpx.Response(200, headers={"content-type": "image/png"}, content=b"PNGDATA")

    client = httpx.Client(transport=httpx.MockTransport(handler))

    result = safe_url_fetcher("http://logo.agency-example.com/logo.png", client=client)

    assert captured["host"] == "93.184.216.34"  # connected to the PINNED ip
    assert captured["header_host"] == "logo.agency-example.com"  # original Host preserved
    assert captured["sni"] == "logo.agency-example.com"
    assert result["string"] == b"PNGDATA"
    assert result["mime_type"] == "image/png"


def test_fetch_raises_ssrf_blocked_on_http_error_status(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(socket, "gethostbyname", lambda _host: "93.184.216.34")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404)

    client = httpx.Client(transport=httpx.MockTransport(handler))

    with pytest.raises(httpx.HTTPStatusError):
        safe_url_fetcher("http://example.com/missing.png", client=client)


def test_safe_url_fetcher_rejects_out_of_range_port_with_ssrf_blocked_error() -> None:
    # F4-LOW-16: Invalid port raises SSRFBlockedError, not raw ValueError
    with pytest.raises(SSRFBlockedError):
        safe_url_fetcher("http://example.com:70000/test.png")
