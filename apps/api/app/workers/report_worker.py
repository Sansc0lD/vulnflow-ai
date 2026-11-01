"""ReportCompilerService / Celery worker — PLAN.md FASE 4.7 (EC-15/EC-16/EC-17).

`compile_report` is the pure orchestration logic (DB session + storage +
renderer all injected), unit-tested directly. `compile_pdf_task` is the
thin Celery wrapper around it that supplies the real dependencies.
"""

import contextlib
import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import QuotaExhaustedError, ResourceNotFoundError
from app.models.finding import Finding
from app.models.project import Project
from app.models.report import Report
from app.models.subscription import Subscription
from app.services.report_renderer import build_report_html, render_html_to_pdf
from app.services.s3_storage import S3StorageClient
from app.workers.celery_app import celery_app


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

    # F4-MED-13 & F4-MED-02: Query curated findings, optionally filtered by finding_ids,
    # capped at 500
    finding_query = db.query(Finding).filter_by(
        project_id=project_id,
        is_curated_for_report=True,
    )
    if finding_ids is not None:
        parsed_ids = [uuid.UUID(fid) if isinstance(fid, str) else fid for fid in finding_ids]
        finding_query = finding_query.filter(Finding.id.in_(parsed_ids))

    findings = finding_query.limit(500).all()
    finding_dicts = [
        {
            "title": f.title,
            "severity": f.severity,
            "cvss_score": float(f.cvss_score),
            "cwe_id": f.cwe_id,
        }
        for f in findings
    ]

    html = build_report_html(
        report_title=report_title,
        client_name=client_name,
        findings=finding_dicts,
        executive_summary=executive_summary,
        business_impact=business_impact,
        watermark_text=watermark_text,
    )
    # If render_fn raises (EC-16: WeasyPrint OOM/PDF bomb), nothing below has
    # run yet — no Report row, no S3 upload, no quota decrement.
    pdf_bytes = render_fn(html)

    report = Report(
        project_id=project_id,
        report_title=report_title,
        storage_path=f"reports/{project_id}/{uuid.uuid4()}.pdf",
        watermark_applied=watermark_text is not None,
    )
    db.add(report)
    db.flush()

    storage.upload_bytes(report.storage_path, pdf_bytes)

    subscription.reports_used_this_month += 1

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
) -> str:
    from app.core.dependencies import get_db
    from app.services.s3_storage import get_s3_bucket_name, make_boto_s3_client

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
        )
        return str(report.id)
    finally:
        db_generator.close()
