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
    html = "<html><body><h1>Hello</h1></body></html>"

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
