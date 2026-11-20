"""ReportCompilerService — PLAN.md FASE 4.7 (WeasyPrint HTML/CSS Paged Media + WCAG 2.1)."""

import math
import re
from html import escape
from typing import Any

from app.services.safe_fetcher import safe_url_fetcher

_HEX_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
_RADAR_AXES: tuple[str, ...] = ("AV", "AC", "PR", "UI", "S", "C", "I", "A")
_RADAR_WEIGHTS: dict[str, dict[str, float]] = {
    "AV": {"N": 1.0, "A": 0.72, "L": 0.5, "P": 0.25},
    "AC": {"L": 1.0, "H": 0.45},
    "PR": {"N": 1.0, "L": 0.65, "H": 0.35},
    "UI": {"N": 1.0, "R": 0.45},
    "S": {"U": 0.55, "C": 1.0},
    "C": {"H": 1.0, "L": 0.55, "N": 0.15},
    "I": {"H": 1.0, "L": 0.55, "N": 0.15},
    "A": {"H": 1.0, "L": 0.55, "N": 0.15},
}


def _sanitize_hex_color(value: str | None, default: str) -> str:
    if value and _HEX_COLOR_RE.match(value.strip()):
        return value.strip()
    return default


def _linearize_channel(channel_8bit: int) -> float:
    c = channel_8bit / 255.0
    if c <= 0.03928:
        return c / 12.92
    return float(((c + 0.055) / 1.055) ** 2.4)


def relative_luminance(hex_color: str) -> float:
    cleaned = _sanitize_hex_color(hex_color, "#0F172A").lstrip("#")
    r = _linearize_channel(int(cleaned[0:2], 16))
    g = _linearize_channel(int(cleaned[2:4], 16))
    b = _linearize_channel(int(cleaned[4:6], 16))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def compute_contrast_ratio(fg_hex: str, bg_hex: str) -> float:
    l1 = relative_luminance(fg_hex)
    l2 = relative_luminance(bg_hex)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return round((lighter + 0.05) / (darker + 0.05), 2)


def pick_accessible_text_color(bg_hex: str) -> str:
    """Return high-contrast white or dark slate text against an arbitrary hex background."""
    white_ratio = compute_contrast_ratio("#FFFFFF", bg_hex)
    dark_ratio = compute_contrast_ratio("#0F172A", bg_hex)
    return "#FFFFFF" if white_ratio >= dark_ratio else "#0F172A"


def _format_port(finding: dict[str, Any]) -> str:
    port = finding.get("target_port")
    if port is None and "port" in finding:
        port = finding.get("port")
    return "N/A" if port is None else str(port)


def _finding_row(finding: dict[str, Any]) -> str:
    sev = str(finding.get("severity", "INFO")).upper()
    host = finding.get("target_host", "")
    port_str = _format_port(finding)
    target_display = f"{host}:{port_str}" if host else port_str
    return (
        "<tr>"
        f"<td>{escape(str(finding.get('title', '')))}</td>"
        f'<td><span class="sev sev-{escape(sev)}">{escape(sev)}</span></td>'
        f"<td>{escape(str(finding.get('cvss_score', '')))}</td>"
        f"<td>{escape(str(finding.get('cwe_id', '')))}</td>"
        f"<td><code>{escape(target_display)}</code></td>"
        "</tr>"
    )


def _finding_detail_block(finding: dict[str, Any]) -> str:
    sev = str(finding.get("severity", "INFO")).upper()
    host = str(finding.get("target_host", ""))
    port_str = _format_port(finding)
    endpoint = str(finding.get("endpoint_path", ""))
    cvss_vector = str(finding.get("cvss_vector", ""))
    steps = finding.get("reproduction_steps") or []
    raw_evidence = str(finding.get("raw_evidence", ""))

    steps_html = ""
    if isinstance(steps, list) and steps:
        items = "".join(f"<li>{escape(str(s))}</li>" for s in steps)
        steps_html = f"<div><strong>Reproduction Steps:</strong><ol>{items}</ol></div>"

    evidence_html = ""
    if raw_evidence:
        evidence_html = (
            f"<div><strong>Technical Evidence (PoC):</strong>"
            f'<pre class="poc">{escape(raw_evidence)}</pre></div>'
        )

    vector_html = (
        f"<div><strong>CVSS Vector:</strong> <code>{escape(cvss_vector)}</code></div>"
        if cvss_vector
        else ""
    )

    return (
        '<div class="finding-card">'
        f'<div class="finding-head"><strong>{escape(str(finding.get("title", "")))}</strong>'
        f' <span class="sev sev-{escape(sev)}">{escape(sev)}</span>'
        f" (CVSS {escape(str(finding.get('cvss_score', '')))})</div>"
        f'<div class="finding-meta">'
        f"<span>CWE: <code>{escape(str(finding.get('cwe_id', '')))}</code></span> · "
        f"<span>Host: <code>{escape(host or 'N/A')}</code></span> · "
        f"<span>Port: <code>{escape(port_str)}</code></span> · "
        f"<span>Path: <code>{escape(endpoint or '/')}</code></span>"
        f"</div>"
        f"{vector_html}"
        f"{steps_html}"
        f"{evidence_html}"
        "</div>"
    )


def _remediation_block(remediations: list[dict[str, Any]] | None) -> str:
    if not remediations:
        return ""
    items = []
    for rem in remediations:
        cwe = escape(str(rem.get("cwe_id", "")))
        title = escape(str(rem.get("vuln_title", "")))
        guidance = escape(str(rem.get("remediation_guidance", "")))
        items.append(f"<li><strong>{cwe} — {title}:</strong> {guidance}</li>")
    return f"<h2>Remediation Priorities</h2><ul>{''.join(items)}</ul>"


def _polar_xy(cx: float, cy: float, angle_deg: float, radius: float) -> tuple[float, float]:
    rad = math.radians(angle_deg - 90.0)
    return round(cx + radius * math.cos(rad), 2), round(cy + radius * math.sin(rad), 2)


def _finding_axis_weights(finding: dict[str, Any]) -> dict[str, float]:
    try:
        score = float(finding.get("cvss_score") or 0.0)
    except (TypeError, ValueError):
        score = 0.0
    fallback = max(0.2, min(1.0, score / 10.0))
    weights = dict.fromkeys(_RADAR_AXES, fallback)

    vector = str(finding.get("cvss_vector") or "").strip()
    if vector:
        for part in vector.split("/"):
            if ":" not in part:
                continue
            key, val = part.split(":", 1)
            axis_map = _RADAR_WEIGHTS.get(key)
            if axis_map and val in axis_map:
                weights[key] = axis_map[val]
    return weights


def _render_cvss_radar_section(
    findings: list[dict[str, Any]], *, primary_color: str, secondary_color: str
) -> str:
    if not findings:
        return ""

    counts: dict[str, int] = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
    scores: list[float] = []
    axis_totals = dict.fromkeys(_RADAR_AXES, 0.0)

    for finding in findings:
        sev = str(finding.get("severity", "INFO")).upper()
        if sev in counts:
            counts[sev] += 1
        try:
            score = float(finding.get("cvss_score") or 0.0)
        except (TypeError, ValueError):
            score = 0.0
        scores.append(score)
        per_finding = _finding_axis_weights(finding)
        for axis in _RADAR_AXES:
            axis_totals[axis] += per_finding[axis]

    count = len(findings)
    avg_score = sum(scores) / count if count else 0.0
    peak_score = max(scores, default=0.0)

    cx, cy, max_r = 120.0, 120.0, 78.0
    step_deg = 360.0 / len(_RADAR_AXES)

    rings_svg = ""
    for scale in (0.33, 0.66, 1.0):
        pts = " ".join(
            f"{_polar_xy(cx, cy, idx * step_deg, max_r * scale)[0]},"
            f"{_polar_xy(cx, cy, idx * step_deg, max_r * scale)[1]}"
            for idx in range(len(_RADAR_AXES))
        )
        rings_svg += f'<polygon points="{pts}" fill="none" stroke="#CBD5E1" stroke-width="1" />'

    spokes_svg = ""
    labels_svg = ""
    data_coords: list[tuple[float, float]] = []
    for idx, axis in enumerate(_RADAR_AXES):
        angle = idx * step_deg
        ox, oy = _polar_xy(cx, cy, angle, max_r)
        spokes_svg += (
            f'<line x1="{cx}" y1="{cy}" x2="{ox}" y2="{oy}" stroke="#CBD5E1" stroke-width="1" />'
        )
        lx, ly = _polar_xy(cx, cy, angle, max_r + 18.0)
        labels_svg += (
            f'<text x="{lx}" y="{ly}" text-anchor="middle" dominant-baseline="central" '
            f'font-family="sans-serif" font-size="9" font-weight="bold" fill="#334155">'
            f"{axis}</text>"
        )
        avg_weight = max(0.15, min(1.0, axis_totals[axis] / count))
        data_coords.append(_polar_xy(cx, cy, angle, max_r * avg_weight))

    data_pts = " ".join(f"{x},{y}" for x, y in data_coords)
    dots_svg = "".join(
        f'<circle cx="{x}" cy="{y}" r="3" fill="{secondary_color}" />' for x, y in data_coords
    )

    svg_html = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 240" width="210" height="210" '
        'role="img" aria-label="CVSS v3.1 Risk Profile Radar">'
        f"{rings_svg}{spokes_svg}"
        f'<polygon points="{data_pts}" fill="{secondary_color}" fill-opacity="0.22" '
        f'stroke="{secondary_color}" stroke-width="2" stroke-linejoin="round" />'
        f"{dots_svg}{labels_svg}"
        f'<circle cx="{cx}" cy="{cy}" r="20" fill="#FFFFFF" stroke="{primary_color}" '
        'stroke-width="1.5" />'
        f'<text x="{cx}" y="{cy - 3}" text-anchor="middle" dominant-baseline="central" '
        f'font-family="sans-serif" font-size="11" font-weight="bold" fill="{primary_color}">'
        f"{avg_score:.1f}</text>"
        f'<text x="{cx}" y="{cy + 9}" text-anchor="middle" dominant-baseline="central" '
        'font-family="sans-serif" font-size="7" fill="#64748B">AVG CVSS</text>'
        "</svg>"
    )

    sev_rows = "".join(
        f'<tr><td><span class="sev sev-{sev}">{sev}</span></td>'
        f"<td><strong>{counts[sev]}</strong></td></tr>"
        for sev in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO")
    )

    return (
        "<h2>CVSS v3.1 Risk Profile</h2>"
        '<table class="radar-layout"><tr>'
        f'<td class="radar-cell">{svg_html}</td>'
        '<td class="radar-metrics">'
        f"<p><strong>Findings in Scope:</strong> {count} · "
        f"<strong>Average CVSS:</strong> {avg_score:.1f} · "
        f"<strong>Peak CVSS:</strong> {peak_score:.1f}</p>"
        "<table><thead><tr><th>Severity</th><th>Count</th></tr></thead>"
        f"<tbody>{sev_rows}</tbody></table>"
        "</td></tr></table>"
    )


def build_report_html(
    *,
    report_title: str,
    client_name: str,
    findings: list[dict[str, Any]],
    executive_summary: str,
    business_impact: str,
    watermark_text: str | None,
    agency_name: str = "VulnFlow AI",
    logo_url: str | None = None,
    primary_color: str = "#0F172A",
    secondary_color: str = "#3B82F6",
    confidentiality_text: str = "",
    show_cover_page: bool = True,
    show_cvss_radar: bool = True,
    remediations: list[dict[str, Any]] | None = None,
    report_version: str = "v1.0",
) -> str:
    safe_primary = _sanitize_hex_color(primary_color, "#0F172A")
    safe_secondary = _sanitize_hex_color(secondary_color, "#3B82F6")
    cover_text_color = pick_accessible_text_color(safe_primary)
    accent_text_color = pick_accessible_text_color(safe_secondary)

    watermark_html = (
        f'<div class="watermark">{escape(watermark_text)}</div>' if watermark_text else ""
    )
    logo_html = (
        f'<img src="{escape(logo_url)}" alt="Agency Logo" class="cover-logo" />' if logo_url else ""
    )
    nda_html = (
        f'<div class="nda-box">{escape(confidentiality_text)}</div>' if confidentiality_text else ""
    )
    cover_html = (
        f"""
        <section class="cover" style="background-color: {safe_primary}; color: {cover_text_color};">
            <div class="cover-top">
                {logo_html}
                <div class="cover-agency">{escape(agency_name)}</div>
            </div>
            <div class="cover-body">
                <div
                    class="cover-badge"
                    style="background-color: {safe_secondary}; color: {accent_text_color};"
                >
                    SECURITY ASSESSMENT REPORT ({escape(report_version)})
                </div>
                <h1 class="cover-title">{escape(report_title)}</h1>
                <p class="cover-client">Prepared for: <strong>{escape(client_name)}</strong></p>
            </div>
            {nda_html}
        </section>
        """
        if show_cover_page
        else ""
    )

    rows = "".join(_finding_row(f) for f in findings)
    detail_cards = "".join(_finding_detail_block(f) for f in findings)
    remediation_html = _remediation_block(remediations)
    radar_html = (
        _render_cvss_radar_section(
            findings, primary_color=safe_primary, secondary_color=safe_secondary
        )
        if show_cvss_radar
        else ""
    )

    return f"""
    <html>
    <head>
        <meta charset="utf-8" />
        <style>
            @page {{
                margin: 20mm;
                @bottom-right {{
                    content: "Page " counter(page) " / " counter(pages);
                    font-size: 9pt;
                    color: #64748b;
                }}
                @bottom-left {{
                    content: "{escape(agency_name)} • {escape(report_version)}";
                    font-size: 9pt;
                    color: #64748b;
                }}
            }}
            body {{ font-family: sans-serif; color: #1e293b; font-size: 10pt; line-height: 1.5; }}
            h1, h2 {{ color: {safe_primary}; }}
            h2 {{
                border-bottom: 2px solid {safe_secondary};
                padding-bottom: 4px;
                margin-top: 22px;
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
            .cover {{
                padding: 36px;
                border-radius: 8px;
                margin-bottom: 24px;
                page-break-after: always;
            }}
            .cover-logo {{ max-height: 56px; max-width: 180px; margin-bottom: 10px; }}
            .cover-agency {{ font-size: 13pt; font-weight: bold; }}
            .cover-badge {{
                display: inline-block;
                padding: 4px 10px;
                border-radius: 4px;
                font-size: 8.5pt;
                font-weight: bold;
                margin-top: 24px;
            }}
            .cover-title {{ font-size: 22pt; margin: 12px 0 8px 0; color: inherit; }}
            .cover-client {{ font-size: 11pt; margin: 0; }}
            .nda-box {{
                margin-top: 28px;
                padding: 10px;
                border: 1px solid rgba(255,255,255,0.25);
                font-size: 8.5pt;
            }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 9pt; }}
            th, td {{
                border: 1px solid #cbd5e1;
                padding: 6px 8px;
                text-align: left;
                vertical-align: top;
            }}
            th {{ background-color: {safe_primary}; color: {cover_text_color}; }}
            table.radar-layout {{ border: none; margin-top: 8px; }}
            table.radar-layout > tbody > tr > td {{
                border: none;
                padding: 0;
                vertical-align: middle;
            }}
            td.radar-cell {{ width: 225px; text-align: center; }}
            td.radar-metrics {{ padding-left: 14px !important; }}
            .sev {{ padding: 2px 6px; border-radius: 3px; font-weight: bold; font-size: 8pt; }}
            .sev-CRITICAL {{ background: #fee2e2; color: #991b1b; }}
            .sev-HIGH {{ background: #ffedd5; color: #9a3412; }}
            .sev-MEDIUM {{ background: #fef9c3; color: #854d0e; }}
            .sev-LOW {{ background: #dcfce7; color: #166534; }}
            .sev-INFO {{ background: #dbeafe; color: #1e40af; }}
            .finding-card {{
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 10px 12px;
                margin-top: 12px;
                page-break-inside: avoid;
                break-inside: avoid;
            }}
            .finding-meta {{ font-size: 8.5pt; color: #475569; margin: 4px 0 8px 0; }}
            pre.poc {{
                background: #0f172a;
                color: #e2e8f0;
                padding: 8px;
                border-radius: 4px;
                font-size: 8pt;
                white-space: pre-wrap;
                word-break: break-all;
            }}
        </style>
    </head>
    <body>
        {watermark_html}
        {cover_html}
        <h1>{escape(report_title)}</h1>
        <p>Client: {escape(client_name)} · Version: {escape(report_version)}</p>
        <h2>Executive Summary</h2>
        <p>{escape(executive_summary)}</p>
        <h2>Business Impact</h2>
        <p>{escape(business_impact)}</p>
        {remediation_html}
        {radar_html}
        <h2>Findings Summary</h2>
        <table>
            <thead><tr><th>Title</th><th>Severity</th><th>CVSS</th><th>CWE</th><th>Target</th></tr></thead>
            <tbody>{rows}</tbody>
        </table>
        <h2>Technical Details &amp; Proof of Concept</h2>
        {detail_cards}
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
    from weasyprint.urls import URLFetcherResponse

    class _WeasyPrintSafeFetcher:
        """Adapt dict-returning safe_url_fetcher to WeasyPrint 70 URLFetcherResponse API."""

        _fail_on_errors: bool = False

        def fetch(self, url: str, headers: dict[str, str] | None = None) -> URLFetcherResponse:
            del headers
            result = safe_url_fetcher(url)
            mime_type = str(result.get("mime_type") or "application/octet-stream")
            return URLFetcherResponse(
                url,
                body=result["string"],
                headers={"Content-Type": mime_type},
            )

        def __call__(self, url: str) -> URLFetcherResponse:
            return self.fetch(url)

    return HTML(string=html, url_fetcher=_WeasyPrintSafeFetcher()).write_pdf()  # type: ignore[no-any-return]
