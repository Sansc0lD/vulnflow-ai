"""ReportCompilerService / Celery worker — PLAN.md FASE 4.7 (EC-15/EC-16/EC-17).

`compile_report` is the pure orchestration logic (DB session + storage +
renderer all injected), unit-tested directly. `compile_pdf_task` is the
thin Celery wrapper around it that supplies the real dependencies.
"""

import base64
import contextlib
import json
import re
import urllib.parse
import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.core.audit import record_audit_log
from app.core.crypto import decrypt_poc, get_encryption_key
from app.core.exceptions import QuotaExhaustedError, ResourceNotFoundError
from app.core.redis_client import get_redis_client
from app.models.finding import Finding
from app.models.project import Project
from app.models.proof_of_concept import ProofOfConcept
from app.models.report import Report
from app.models.subscription import Subscription
from app.models.workspace import Workspace
from app.services.report_renderer import build_report_html, render_html_to_pdf
from app.services.s3_storage import S3StorageClient
from app.workers.celery_app import celery_app

_SEVERITY_RANK = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
_JOB_STATUS_TTL_SECONDS = 24 * 3600


def _try_get_encryption_key() -> bytes | None:
    try:
        return get_encryption_key()
    except RuntimeError:
        return None


def _resolve_logo_for_pdf(
    storage: Any, workspace_id: uuid.UUID, logo_url: str | None
) -> str | None:
    """Resolve workspace-owned S3 logo URLs directly from internal storage as a data URI.

    Uploaded workspace logos use `S3_PUBLIC_ENDPOINT_URL` so browsers can display them,
    which WeasyPrint's anti-SSRF `safe_url_fetcher` blocks when pointing at loopback or
    Docker-private addresses. Reading the workspace-scoped object directly keeps SSRF
    protection intact while embedding the agency logo reliably.
    """
    if not logo_url:
        return None
    if logo_url.startswith("data:"):
        return logo_url

    parsed_path = urllib.parse.urlsplit(logo_url).path
    match = re.search(
        rf"(workspaces/{re.escape(str(workspace_id))}/logo\.(?:png|jpg|jpeg|svg))$",
        parsed_path,
    )
    if match:
        download_fn = getattr(storage, "download_bytes", None)
        if not callable(download_fn):
            return logo_url
        fetched = download_fn(match.group(1))
        if fetched is None:
            return None
        raw_bytes, content_type = fetched
        encoded = base64.b64encode(raw_bytes).decode("ascii")
        return f"data:{content_type};base64,{encoded}"

    return logo_url


def _decrypt_finding_pocs(
    db: Session, finding_ids: list[uuid.UUID]
) -> dict[uuid.UUID, tuple[str, list[str]]]:
    if not finding_ids:
        return {}
    pocs = db.query(ProofOfConcept).filter(ProofOfConcept.finding_id.in_(finding_ids)).all()
    if not pocs:
        return {}
    key = _try_get_encryption_key()
    result: dict[uuid.UUID, tuple[str, list[str]]] = {}
    for poc in pocs:
        raw_text = ""
        if key is not None:
            with contextlib.suppress(Exception):
                raw_text = decrypt_poc(
                    poc.encrypted_raw_evidence,
                    key,
                    poc.iv_nonce,
                    poc.auth_tag,
                ).decode("utf-8", errors="replace")
        steps = list(poc.reproduction_steps or [])
        result[poc.finding_id] = (raw_text, steps)
    return result


def compile_report(
    db: Session,
    storage: S3StorageClient | Any,
    *,
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    report_title: str,
    executive_summary: str,
    business_impact: str,
    watermark_text: str | None,
    finding_ids: list[str] | None = None,
    theme_options: dict[str, Any] | None = None,
    remediations: list[dict[str, Any]] | None = None,
    render_fn: Callable[[str], bytes] = render_html_to_pdf,
) -> Report:
    # F4-LOW-02 & F4-HIGH-09: Fail-closed subscription lookup with row lock
    subscription = (
        db.query(Subscription).filter_by(workspace_id=workspace_id).with_for_update().one_or_none()
    )
    if subscription is None:
        raise QuotaExhaustedError("No active subscription found for this workspace.")

    # F4-HIGH-10: Check monthly quota reset date
    now = datetime.now(UTC)
    if subscription.quota_reset_date is not None:
        reset_date = subscription.quota_reset_date
        if reset_date.tzinfo is None:
            reset_date = reset_date.replace(tzinfo=UTC)
        if now >= reset_date:
            subscription.reports_used_this_month = 0
            subscription.quota_reset_date = now + timedelta(days=30)

    if subscription.reports_used_this_month >= subscription.monthly_report_quota:
        raise QuotaExhaustedError("Monthly report compilation quota exhausted.")

    # F4-LOW-03: Ensure project exists and belongs to workspace
    project = db.query(Project).filter_by(id=project_id, workspace_id=workspace_id).one_or_none()
    if project is None:
        raise ResourceNotFoundError(
            f"Project '{project_id}' not found in workspace '{workspace_id}'."
        )
    client_name = project.client_name
    workspace = db.get(Workspace, workspace_id)

    # BL-02 + EC-12: Exclude quarantined (out-of-scope) and FALSE_POSITIVE findings from PDF.
    # Explicit `finding_ids` selected in the UI are honored while still enforcing quarantine
    # and false-positive guards; omitted `finding_ids` defaults to curated findings only.
    finding_query = db.query(Finding).filter(
        Finding.project_id == project_id,
        Finding.is_quarantined.is_(False),
        Finding.status != "FALSE_POSITIVE",
    )
    if finding_ids is not None:
        parsed_ids = [uuid.UUID(fid) if isinstance(fid, str) else fid for fid in finding_ids]
        finding_query = finding_query.filter(Finding.id.in_(parsed_ids))
    else:
        finding_query = finding_query.filter(Finding.is_curated_for_report.is_(True))

    findings = finding_query.limit(500).all()
    findings.sort(key=lambda f: (_SEVERITY_RANK.get(f.severity, 99), -float(f.cvss_score)))
    poc_map = _decrypt_finding_pocs(db, [f.id for f in findings])

    finding_dicts = []
    for f in findings:
        raw_evidence, steps = poc_map.get(f.id, ("", []))
        finding_dicts.append(
            {
                "title": f.title,
                "severity": f.severity,
                "cvss_score": float(f.cvss_score),
                "cvss_vector": f.cvss_vector,
                "cwe_id": f.cwe_id,
                "target_host": f.target_host,
                "target_port": f.target_port,
                "endpoint_path": f.endpoint_path,
                "raw_evidence": raw_evidence,
                "reproduction_steps": steps,
            }
        )

    existing_reports_count = db.query(Report).filter_by(project_id=project_id).count()
    report_version = f"v1.{existing_reports_count}"

    is_paid_tier = subscription.tier != "FREE"
    agency_name = workspace.name if (is_paid_tier and workspace is not None) else "VulnFlow AI"
    raw_logo_url = workspace.custom_logo_url if (is_paid_tier and workspace is not None) else None
    logo_url = _resolve_logo_for_pdf(storage, workspace_id, raw_logo_url)
    primary_color = (
        workspace.brand_primary_color if (is_paid_tier and workspace is not None) else "#0F172A"
    )
    secondary_color = (
        workspace.brand_secondary_color if (is_paid_tier and workspace is not None) else "#3B82F6"
    )
    confidentiality_text = (
        (workspace.confidentiality_text or "") if (is_paid_tier and workspace is not None) else ""
    )
    show_cover_page = bool(theme_options.get("show_cover_page", True)) if theme_options else True
    show_cvss_radar = bool(theme_options.get("show_cvss_radar", True)) if theme_options else True
    if is_paid_tier and theme_options:
        primary_color = str(theme_options.get("primary_color") or primary_color)
        secondary_color = str(theme_options.get("secondary_color") or secondary_color)
        if theme_options.get("confidentiality_notice"):
            confidentiality_text = str(theme_options["confidentiality_notice"])

    html = build_report_html(
        report_title=report_title,
        client_name=client_name,
        findings=finding_dicts,
        executive_summary=executive_summary,
        business_impact=business_impact,
        watermark_text=watermark_text,
        agency_name=agency_name,
        logo_url=logo_url,
        primary_color=primary_color,
        secondary_color=secondary_color,
        confidentiality_text=confidentiality_text,
        show_cover_page=show_cover_page,
        show_cvss_radar=show_cvss_radar,
        remediations=remediations,
        report_version=report_version,
    )
    # If render_fn raises (EC-16: WeasyPrint OOM/PDF bomb), nothing below has
    # run yet — no Report row, no S3 upload, no quota decrement.
    pdf_bytes = render_fn(html)

    report = Report(
        project_id=project_id,
        report_title=report_title,
        version=report_version,
        storage_path=f"reports/{project_id}/{uuid.uuid4()}.pdf",
        watermark_applied=watermark_text is not None,
    )
    db.add(report)
    db.flush()

    storage.upload_bytes(report.storage_path, pdf_bytes)

    subscription.reports_used_this_month += 1
    record_audit_log(
        db,
        workspace_id=workspace_id,
        actor_user_id=None,
        action="REPORT_COMPILED",
        target_entity="reports",
        ip_address="worker",
        details={
            "report_id": str(report.id),
            "project_id": str(project_id),
            "version": report_version,
            "findings_count": len(finding_dicts),
        },
    )

    # F4-LOW-04: If DB commit fails, rollback and cleanup S3 object to prevent orphaned storage
    try:
        db.commit()
    except Exception:
        db.rollback()
        if hasattr(storage, "delete_file"):
            with contextlib.suppress(Exception):
                storage.delete_file(report.storage_path)
        raise

    return report


def _update_job_status(
    job_id: str | None,
    *,
    workspace_id: str,
    status: str,
    progress_percentage: int,
    report_id: str | None = None,
    error_message: str | None = None,
) -> None:
    if not job_id:
        return
    with contextlib.suppress(Exception):
        redis_client = get_redis_client()
        payload = {
            "job_id": job_id,
            "workspace_id": workspace_id,
            "status": status,
            "progress_percentage": progress_percentage,
            "report_id": report_id,
            "error_message": error_message,
        }
        redis_client.set(
            f"job:report:{job_id}",
            json.dumps(payload),
            ex=_JOB_STATUS_TTL_SECONDS,
        )


@celery_app.task(bind=True)  # type: ignore[untyped-decorator] # celery ships no stubs
def compile_pdf_task(
    self: Any,
    *,
    workspace_id: str,
    project_id: str,
    report_title: str,
    executive_summary: str,
    business_impact: str,
    watermark_text: str | None,
    finding_ids: list[str] | None = None,
    theme_options: dict[str, Any] | None = None,
    remediations: list[dict[str, Any]] | None = None,
) -> str:
    from app.core.dependencies import get_db
    from app.services.s3_storage import get_s3_bucket_name, make_boto_s3_client

    task_id = str(getattr(self.request, "id", "") or "")
    _update_job_status(
        task_id, workspace_id=workspace_id, status="PROCESSING", progress_percentage=50
    )

    db_generator = get_db()
    db = next(db_generator)
    try:
        storage = S3StorageClient(make_boto_s3_client(), bucket=get_s3_bucket_name())
        report = compile_report(
            db,
            storage,
            workspace_id=uuid.UUID(workspace_id),
            project_id=uuid.UUID(project_id),
            report_title=report_title,
            executive_summary=executive_summary,
            business_impact=business_impact,
            watermark_text=watermark_text,
            finding_ids=finding_ids,
            theme_options=theme_options,
            remediations=remediations,
        )
        _update_job_status(
            task_id,
            workspace_id=workspace_id,
            status="COMPLETED",
            progress_percentage=100,
            report_id=str(report.id),
        )
        return str(report.id)
    except Exception as exc:
        _update_job_status(
            task_id,
            workspace_id=workspace_id,
            status="FAILED",
            progress_percentage=0,
            error_message=str(exc),
        )
        raise
    finally:
        db_generator.close()
