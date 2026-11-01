"""ReportCompilerService — PLAN.md FASE 4.7 (WeasyPrint HTML/CSS Paged Media)."""

from html import escape
from typing import Any

from app.services.safe_fetcher import safe_url_fetcher


def _finding_row(finding: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{escape(str(finding.get('title', '')))}</td>"
        f"<td>{escape(str(finding.get('severity', '')))}</td>"
        f"<td>{escape(str(finding.get('cvss_score', '')))}</td>"
        f"<td>{escape(str(finding.get('cwe_id', '')))}</td>"
        "</tr>"
    )


def build_report_html(
    *,
    report_title: str,
    client_name: str,
    findings: list[dict[str, Any]],
    executive_summary: str,
    business_impact: str,
    watermark_text: str | None,
) -> str:
    watermark_html = (
        f'<div class="watermark">{escape(watermark_text)}</div>' if watermark_text else ""
    )
    rows = "".join(_finding_row(f) for f in findings)
    return f"""
    <html>
    <head>
        <style>
            @page {{
                margin: 20mm;
                @bottom-right {{ content: counter(page); }}
            }}
            .watermark {{
                position: fixed;
                top: 40%;
                left: 5%;
                width: 90%;
                text-align: center;
                transform: rotate(-45deg);
                transform-origin: center;
                font-size: 54pt;
                font-weight: bold;
                color: rgba(220, 38, 38, 0.18);
                z-index: 9999;
                pointer-events: none;
                text-transform: uppercase;
                letter-spacing: 4px;
            }}
        </style>
    </head>
    <body>
        {watermark_html}
        <h1>{escape(report_title)}</h1>
        <p>Klien: {escape(client_name)}</p>
        <h2>Ringkasan Eksekutif</h2>
        <p>{escape(executive_summary)}</p>
        <h2>Dampak Bisnis</h2>
        <p>{escape(business_impact)}</p>
        <h2>Daftar Temuan</h2>
        <table>
            <thead><tr><th>Judul</th><th>Severity</th><th>CVSS</th><th>CWE</th></tr></thead>
            <tbody>{rows}</tbody>
        </table>
    </body>
    </html>
    """


def render_html_to_pdf(html: str) -> bytes:
    # Deferred import: WeasyPrint needs native GTK3/Pango/Cairo libraries
    # (present in the Linux Docker deployment target per docker-compose.yml
    # / SDD prerequisites) that aren't necessarily installed on every dev
    # machine this module gets imported on — a lazy import here means a
    # missing native lib only breaks actual rendering, not every caller of
    # this module (router wiring, Celery task registration, etc.).
    from weasyprint import HTML

    return HTML(string=html, url_fetcher=safe_url_fetcher).write_pdf()  # type: ignore[no-any-return]
