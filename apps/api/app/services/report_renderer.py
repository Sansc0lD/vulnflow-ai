"""ReportCompilerService — Modular Jinja2 WeasyPrint HTML/CSS Paged Media + WCAG 2.1."""

import math
import re
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.domain.fallback import load_catalog
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

_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates" / "report"
_JINJA_ENV = Environment(
    loader=FileSystemLoader(_TEMPLATES_DIR),
    autoescape=select_autoescape(["html", "xml"]),
    trim_blocks=True,
    lstrip_blocks=True,
)

_REPORT_LABELS: dict[str, dict[str, str]] = {
    "en": {
        "client": "Client",
        "version": "Version",
        "report_version": "Report Version",
        "prepared_for": "Prepared for",
        "prepared_by": "Prepared By",
        "generated_date": "Generated Date",
        "engagement_window": "Engagement Window",
        "authorized_scope": "Authorized Scope",
        "confidential_deliverable": "Confidential Security Deliverable",
        "confidentiality_statement": "Confidentiality Notice",
        "doc_control": "Document Control",
        "document_title": "Document Title",
        "classification": "Classification",
        "toc": "Table of Contents",
        "executive_summary": "Executive Summary",
        "business_impact": "Business Impact",
        "methodology_and_scope": "Scope & Assessment Methodology",
        "framework": "Methodology Framework",
        "methodology_intro": (
            "Testing followed structured reconnaissance, automated scanning, manual verification, "
            "and CVSS v3.1 risk rating aligned with the authorized engagement window."
        ),
        "severity": "Severity",
        "sla_target": "Recommended SLA",
        "count": "Findings",
        "findings_summary": "Findings Summary",
        "title": "Title",
        "target": "Target",
        "remediation_priorities": "Remediation Priorities",
        "technical_details": "Technical Details & Proof of Concept",
        "reproduction_steps": "Reproduction Steps:",
        "technical_evidence": "Technical Evidence (PoC):",
        "poc_screenshots": "Proof of Concept Screenshots:",
        "conclusion_and_appendix": "Conclusion & Reference Appendix",
        "conclusion_body": (
            "Remediation efforts should prioritize Critical and High severity exposures first, "
            "followed by re-testing to confirm fixes prior to closure."
        ),
        "appendix_cwe": "Appendix A: CWE Classification Reference",
        "authenticity_verification": "Document Provenance & Authenticity",
        "verification_id": "Verification ID",
        "verify_at": "Verify Online",
        "page": "Page",
    },
    "id": {
        "client": "Klien",
        "version": "Versi",
        "report_version": "Versi Laporan",
        "prepared_for": "Disiapkan untuk",
        "prepared_by": "Disusun Oleh",
        "generated_date": "Tanggal Terbit",
        "engagement_window": "Periode Pengujian",
        "authorized_scope": "Ruang Lingkup Sah",
        "confidential_deliverable": "Dokumen Keamanan Rahasia",
        "confidentiality_statement": "Pernyataan Kerahasiaan",
        "doc_control": "Kontrol Dokumen",
        "document_title": "Judul Dokumen",
        "classification": "Klasifikasi",
        "toc": "Daftar Isi",
        "executive_summary": "Ringkasan Eksekutif",
        "business_impact": "Dampak Bisnis",
        "methodology_and_scope": "Ruang Lingkup & Metodologi Pengujian",
        "framework": "Kerangka Metodologi",
        "methodology_intro": (
            "Pengujian dilakukan melalui tahap pengintaian, pemindaian terstruktur, verifikasi "
            "manual, dan penilaian risiko CVSS v3.1 sesuai jendela otorisasi."
        ),
        "severity": "Tingkat Keparahan",
        "sla_target": "Target SLA Perbaikan",
        "count": "Temuan",
        "findings_summary": "Ringkasan Temuan",
        "title": "Judul Temuan",
        "target": "Target",
        "remediation_priorities": "Prioritas Remediasi",
        "technical_details": "Detail Teknis & Bukti Eksploitasi (PoC)",
        "reproduction_steps": "Langkah Reproduksi:",
        "technical_evidence": "Bukti Teknis (PoC):",
        "poc_screenshots": "Tangkapan Layar Bukti (PoC):",
        "conclusion_and_appendix": "Kesimpulan & Lampiran Referensi",
        "conclusion_body": (
            "Prioritaskan perbaikan kerentanan berkategori Critical dan High terlebih dahulu, "
            "lalu lakukan uji ulang (re-test) untuk memverifikasi efektivitas mitigasi."
        ),
        "appendix_cwe": "Lampiran A: Referensi Klasifikasi CWE",
        "authenticity_verification": "Verifikasi Keaslian Dokumen",
        "verification_id": "Kode Verifikasi",
        "verify_at": "Verifikasi Online",
        "page": "Halaman",
    },
}


def _sanitize_hex_color(value: str | None, default: str) -> str:
    if value and _HEX_COLOR_RE.match(value.strip()):
        return value.strip()
    return default


def _escape_css_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ").replace("\r", " ")


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


def _compute_severity_counts(findings: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
    for finding in findings:
        sev = str(finding.get("severity", "INFO")).upper()
        if sev in counts:
            counts[sev] += 1
    return counts


def _render_cvss_radar_section(
    findings: list[dict[str, Any]], *, primary_color: str, secondary_color: str
) -> str:
    if not findings:
        return ""

    counts = _compute_severity_counts(findings)
    scores: list[float] = []
    axis_totals = dict.fromkeys(_RADAR_AXES, 0.0)

    for finding in findings:
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


def _format_scope_summary(target_scope: list[str] | None) -> str:
    if not target_scope:
        return "Authorized Project Targets"
    cleaned = [entry.strip() for entry in target_scope if entry and entry.strip()]
    if not cleaned:
        return "Authorized Project Targets"
    if len(cleaned) > 3:
        return f"{', '.join(cleaned[:3])} (+{len(cleaned) - 3} more)"
    return ", ".join(cleaned)


def _normalize_finding_for_template(finding: dict[str, Any]) -> dict[str, Any]:
    sev = str(finding.get("severity", "INFO")).upper()
    host = str(finding.get("target_host", ""))
    port_str = _format_port(finding)
    target_display = f"{host}:{port_str}" if host else port_str
    steps = finding.get("reproduction_steps")
    raw_att = finding.get("poc_attachments")
    return {
        "title": str(finding.get("title", "")),
        "severity": sev,
        "cvss_score": finding.get("cvss_score", ""),
        "cvss_vector": str(finding.get("cvss_vector", "")),
        "cwe_id": str(finding.get("cwe_id", "")),
        "host_display": host or "N/A",
        "port_display": port_str,
        "path_display": str(finding.get("endpoint_path", "")) or "/",
        "target_display": target_display,
        "reproduction_steps": list(steps) if isinstance(steps, list) else [],
        "raw_evidence": str(finding.get("raw_evidence", "")),
        "poc_attachments": list(raw_att) if isinstance(raw_att, list) else [],
    }


def _build_cwe_glossary(findings: list[dict[str, Any]]) -> list[dict[str, str]]:
    catalog = load_catalog()
    seen: set[str] = set()
    glossary: list[dict[str, str]] = []
    for f in findings:
        cwe = str(f.get("cwe_id") or "").strip()
        if not cwe or cwe in seen:
            continue
        seen.add(cwe)
        entry = catalog.get(cwe)
        title = entry["title"] if entry is not None else "Security Weakness Classification"
        glossary.append({"cwe_id": cwe, "title": title})
    return glossary


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
    show_toc: bool = True,
    show_methodology: bool = True,
    show_poc_attachments: bool = True,
    report_language: str = "en",
    methodology_framework: str = "OWASP WSTG & PTES",
    remediations: list[dict[str, Any]] | None = None,
    report_version: str = "v1.0",
    target_scope: list[str] | None = None,
    engagement_period: str | None = None,
    generated_date: str | None = None,
    verification_code: str | None = None,
    verification_url: str | None = None,
    verification_qr_data_uri: str | None = None,
) -> str:
    safe_primary = _sanitize_hex_color(primary_color, "#0F172A")
    safe_secondary = _sanitize_hex_color(secondary_color, "#3B82F6")
    cover_text_color = pick_accessible_text_color(safe_primary)
    accent_text_color = pick_accessible_text_color(safe_secondary)
    is_light_cover_text = cover_text_color == "#FFFFFF"
    cover_divider = "rgba(255, 255, 255, 0.22)" if is_light_cover_text else "rgba(15, 23, 42, 0.22)"
    cover_surface = "rgba(255, 255, 255, 0.08)" if is_light_cover_text else "rgba(15, 23, 42, 0.06)"

    lang_key = "id" if report_language == "id" else "en"
    labels = _REPORT_LABELS[lang_key]

    nda_copy = (
        confidentiality_text.strip()
        or "Confidential: Prepared exclusively for authorized client stakeholders."
    )
    cover_top_tag = "FREE TIER PREVIEW" if watermark_text else f"CONFIDENTIAL · {report_version}"
    scope_entries = [s.strip() for s in (target_scope or []) if s and s.strip()]
    if not scope_entries:
        scope_entries = ["Authorized Project Targets"]
    scope_summary = _format_scope_summary(target_scope)
    date_display = (
        generated_date.strip() if generated_date and generated_date.strip() else "Standard Export"
    )
    normalized_findings = [_normalize_finding_for_template(f) for f in findings]
    severity_counts = _compute_severity_counts(normalized_findings)
    cvss_radar_html = (
        _render_cvss_radar_section(
            findings, primary_color=safe_primary, secondary_color=safe_secondary
        )
        if show_cvss_radar
        else ""
    )

    verify_footer = f" · ID {verification_code}" if verification_code else ""
    template = _JINJA_ENV.get_template("base.html")
    return template.render(
        report_title=report_title,
        report_title_css=_escape_css_string(report_title),
        top_right_tag_css=_escape_css_string(cover_top_tag),
        page_label_css=_escape_css_string(labels["page"]),
        agency_name_css=_escape_css_string(agency_name),
        report_version_css=_escape_css_string(report_version),
        verify_footer_css=_escape_css_string(verify_footer),
        client_name=client_name,
        agency_name=agency_name,
        logo_url=logo_url,
        safe_primary=safe_primary,
        safe_secondary=safe_secondary,
        cover_text_color=cover_text_color,
        accent_text_color=accent_text_color,
        cover_divider=cover_divider,
        cover_surface=cover_surface,
        watermark_text=watermark_text,
        nda_copy=nda_copy,
        cover_top_tag=cover_top_tag,
        report_version=report_version,
        generated_date=date_display,
        engagement_period=engagement_period.strip() if engagement_period else "",
        scope_summary=scope_summary,
        scope_entries=scope_entries,
        methodology_framework=methodology_framework,
        executive_summary=executive_summary,
        business_impact=business_impact,
        remediations=remediations or [],
        findings=normalized_findings,
        severity_counts=severity_counts,
        cwe_glossary=_build_cwe_glossary(normalized_findings),
        cvss_radar_html=cvss_radar_html,
        show_cover_page=show_cover_page,
        show_cvss_radar=show_cvss_radar,
        show_toc=show_toc,
        show_methodology=show_methodology,
        show_poc_attachments=show_poc_attachments,
        labels=labels,
        verification_code=verification_code,
        verification_url=verification_url,
        verification_qr_data_uri=verification_qr_data_uri,
    )


def render_html_to_pdf(html: str) -> bytes:
    # Deferred import: WeasyPrint needs native GTK3/Pango/Cairo libraries
    # present in the Linux Docker deployment target.
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
