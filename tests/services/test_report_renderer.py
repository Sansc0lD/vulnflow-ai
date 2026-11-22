"""PLAN.md FASE 4.7 — PDF report rendering (WeasyPrint + SafeURLFetcher wiring)."""

import pytest
from app.services.report_renderer import build_report_html, render_html_to_pdf


def test_build_report_html_includes_finding_and_narrative_content() -> None:
    html = build_report_html(
        report_title="Laporan Audit Bank XYZ",
        client_name="Bank XYZ",
        findings=[
            {
                "title": "SQL Injection",
                "severity": "CRITICAL",
                "cvss_score": 9.8,
                "cwe_id": "CWE-89",
            }
        ],
        executive_summary="Ringkasan eksekutif.",
        business_impact="Dampak bisnis.",
        watermark_text=None,
    )

    assert "Laporan Audit Bank XYZ" in html
    assert "SQL Injection" in html
    assert "Ringkasan eksekutif." in html


def test_build_report_html_includes_watermark_when_provided() -> None:
    html = build_report_html(
        report_title="T",
        client_name="C",
        findings=[],
        executive_summary="",
        business_impact="",
        watermark_text="FREE TIER PREVIEW",
    )

    assert "FREE TIER PREVIEW" in html
    assert "rotate(-45deg)" in html
    assert "position: fixed" in html


def test_render_html_to_pdf_produces_valid_pdf_bytes() -> None:
    tiny_png_b64 = (
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
        "+A8AAQUBAScY42YAAAAASUVORK5CYII="
    )
    html = (
        "<html><body><h1>Hello</h1>"
        f'<img src="data:image/png;base64,{tiny_png_b64}" alt="logo" />'
        "</body></html>"
    )

    try:
        pdf_bytes = render_html_to_pdf(html)
    except OSError as exc:
        # WeasyPrint needs native GTK3/Pango/Cairo libs not installed on
        # every dev machine (they ARE present in the Linux Docker deployment
        # target — see docker-compose.yml / SDD prerequisites). Don't mask a
        # real regression as an environment issue: only skip for the
        # specific native-library-load failure, not an arbitrary OSError.
        if "cannot load library" not in str(exc):
            raise
        pytest.skip(f"WeasyPrint native libraries unavailable in this environment: {exc}")
        return

    assert pdf_bytes.startswith(b"%PDF")


def test_wcag_contrast_and_rich_sections() -> None:
    from app.services.report_renderer import compute_contrast_ratio, pick_accessible_text_color

    assert compute_contrast_ratio("#000000", "#ffffff") > 20.0
    assert pick_accessible_text_color("#ffffff") == "#0F172A"
    assert pick_accessible_text_color("#0f172a") == "#FFFFFF"

    html = build_report_html(
        report_title="Rich Report",
        client_name="Client A",
        findings=[
            {
                "title": "XSS",
                "severity": "HIGH",
                "cvss_score": 7.5,
                "cwe_id": "CWE-79",
                "target_host": "app.client.com",
                "target_port": None,
                "raw_evidence": "GET /?q=<script>",
                "reproduction_steps": ["Send payload"],
            }
        ],
        executive_summary="Summary",
        business_impact="Impact",
        watermark_text=None,
        agency_name="CyberSec Labs",
        primary_color="#0f172a",
        secondary_color="#2563eb",
        confidentiality_text="NDA Clause",
        report_version="v1.2",
        remediations=[{"cwe_id": "CWE-79", "vuln_title": "XSS", "remediation_guidance": "Escape"}],
    )
    assert "CyberSec Labs" in html
    assert "NDA Clause" in html
    assert "v1.2" in html
    assert "app.client.com:N/A" in html
    assert "Send payload" in html
    assert "<h2>Executive Summary</h2>" in html
    assert "<h2>Business Impact</h2>" in html
    assert "<h2>Remediation Priorities</h2>" in html
    assert "<h2>Findings Summary</h2>" in html
    assert "<h2>Technical Details &amp; Proof of Concept</h2>" in html
    assert "Reproduction Steps:" in html
    assert "<svg" in html
    assert "CVSS v3.1 Risk Profile Radar" in html

    html_no_radar = build_report_html(
        report_title="No Radar",
        client_name="Client A",
        findings=[
            {
                "title": "XSS",
                "severity": "HIGH",
                "cvss_score": 7.5,
                "cwe_id": "CWE-79",
                "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N",
            }
        ],
        executive_summary="Summary",
        business_impact="Impact",
        watermark_text=None,
        show_cvss_radar=False,
    )
    assert "CVSS v3.1 Risk Profile Radar" not in html_no_radar
    assert "<svg" not in html_no_radar


def test_cover_page_uses_full_bleed_named_page_and_metadata() -> None:
    html = build_report_html(
        report_title="Core Banking Q4 Assessment",
        client_name="Bank Nusantara",
        findings=[
            {"title": "SQLi", "severity": "CRITICAL", "cvss_score": 9.8, "cwe_id": "CWE-89"},
            {"title": "XSS", "severity": "HIGH", "cvss_score": 7.4, "cwe_id": "CWE-79"},
            {"title": "TLS", "severity": "LOW", "cvss_score": 3.1, "cwe_id": "CWE-326"},
        ],
        executive_summary="Exec summary.",
        business_impact="Business impact.",
        watermark_text="FREE TIER PREVIEW",
        target_scope=["api.bank.local", "auth.bank.local", "10.0.0.0/24", "portal.bank.local"],
        engagement_period="01 Nov 2026 - 15 Nov 2026 (Asia/Jakarta)",
        generated_date="22 Nov 2026",
        show_cvss_radar=False,
    )

    assert "@page cover" in html
    assert "page: cover;" in html
    assert "height: 297mm;" in html
    assert "white-space: nowrap;" in html
    assert "api.bank.local, auth.bank.local, 10.0.0.0/24 (+1 more)" in html
    assert "01 Nov 2026 - 15 Nov 2026 (Asia/Jakarta)" in html
    assert "22 Nov 2026" in html
    assert "cover-sev-table" not in html
    assert "cover-sev-count" not in html
    assert "<svg" not in html
