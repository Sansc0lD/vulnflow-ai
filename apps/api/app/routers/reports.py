"""ReportRouter — PLAN.md FASE 4.7 (SDD §2.6.1.5; EC-15/EC-16/EC-17)."""

import json
import uuid
from datetime import UTC, datetime
from typing import Annotated, Any, Literal, Protocol

from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_workspace_role
from app.core.exceptions import (
    QuotaExhaustedError,
    ResourceNotFoundError,
    ValidationFailedError,
)
from app.core.redis_client import DistributedLock, get_redis_client
from app.models.ai_narrative import AINarrative
from app.models.project import Project
from app.models.report import Report
from app.models.subscription import Subscription
from app.models.workspace_member import WorkspaceMember
from app.services.s3_storage import (
    S3StorageClient,
    get_s3_bucket_name,
    make_public_boto_s3_client,
)
from vulnflow_contracts import (
    CompilePDFAcceptedResponse,
    CompilePDFRequest,
    ReportDownloadResponse,
    ReportJobStatus,
    ReportJobStatusResponse,
    ReportSummaryResponse,
)

router = APIRouter(
    prefix="/api/v1/workspaces/{workspace_id}/projects/{project_id}/reports", tags=["reports"]
)
workspace_reports_router = APIRouter(
    prefix="/api/v1/workspaces/{workspace_id}/reports", tags=["reports"]
)

_require_requester_role = require_workspace_role({"MANAGER", "PENTESTER"})
_require_any_member = require_workspace_role({"MANAGER", "PENTESTER", "VIEWER"})

LOCK_TTL_SECONDS = 10
PRESIGNED_URL_TTL_SECONDS = 900  # 15 minutes, EC-17
_JOB_STATUS_TTL_SECONDS = 24 * 3600


class ReportEnqueuer(Protocol):
    def __call__(self, **kwargs: Any) -> str: ...


def get_report_storage() -> S3StorageClient:
    """Default (production) storage client — overridden in tests."""
    return S3StorageClient(make_public_boto_s3_client(), bucket=get_s3_bucket_name())


def get_report_enqueuer() -> ReportEnqueuer:
    """Default (production) enqueuer — hands off to the real Celery task.
    Overridden in tests so no live Redis broker is required."""
    from app.workers.report_worker import compile_pdf_task

    def _enqueue(**kwargs: Any) -> str:
        result: Any = compile_pdf_task.delay(**kwargs)
        return str(result.id)

    return _enqueue


def _check_subscription_quota_preflight(db: Session, workspace_id: uuid.UUID) -> Subscription:
    subscription = db.query(Subscription).filter_by(workspace_id=workspace_id).one_or_none()
    if subscription is None:
        raise QuotaExhaustedError("No active subscription found for this workspace.")

    now = datetime.now(UTC)
    quota_elapsed = False
    if subscription.quota_reset_date is not None:
        reset_date = subscription.quota_reset_date
        if reset_date.tzinfo is None:
            reset_date = reset_date.replace(tzinfo=UTC)
        quota_elapsed = now >= reset_date

    if (
        not quota_elapsed
        and subscription.reports_used_this_month >= subscription.monthly_report_quota
    ):
        raise QuotaExhaustedError("Monthly report compilation quota exhausted.")
    return subscription


@router.get("", response_model=list[ReportSummaryResponse])
def list_project_reports(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    _member: WorkspaceMember = Depends(_require_any_member),
) -> list[ReportSummaryResponse]:
    project = db.query(Project).filter_by(id=project_id, workspace_id=workspace_id).one_or_none()
    if project is None:
        raise ResourceNotFoundError("Project not found in this workspace.")

    reports = (
        db.query(Report).filter_by(project_id=project_id).order_by(Report.generated_at.desc()).all()
    )
    return [
        ReportSummaryResponse(
            id=str(report.id),
            project_id=str(report.project_id),
            report_title=report.report_title,
            version=report.version,
            watermark_applied=report.watermark_applied,
            generated_at=report.generated_at,
            download_url=f"/api/v1/workspaces/{workspace_id}/reports/{report.id}/download",
        )
        for report in reports
    ]


@router.post("/compile-pdf", response_model=CompilePDFAcceptedResponse, status_code=202)
def compile_pdf(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    payload: CompilePDFRequest,
    db: Session = Depends(get_db),
    redis_client: Any = Depends(get_redis_client),
    enqueue: ReportEnqueuer = Depends(get_report_enqueuer),
    _member: WorkspaceMember = Depends(_require_requester_role),
) -> CompilePDFAcceptedResponse:
    project = db.query(Project).filter_by(id=project_id, workspace_id=workspace_id).one_or_none()
    if project is None:
        raise ResourceNotFoundError("Project not found in this workspace.")

    for fid in payload.finding_ids:
        try:
            uuid.UUID(fid)
        except ValueError as exc:
            raise ValidationFailedError(f"Invalid UUID in finding_ids: {exc}") from exc

    subscription = _check_subscription_quota_preflight(db, workspace_id)

    lock = DistributedLock(
        redis_client, key=f"lock:report:{project_id}", ttl_seconds=LOCK_TTL_SECONDS
    )
    job_id = lock.current_holder()
    if job_id is None:
        # F4-MED-01: Take temporary lock to prevent concurrent requests from double enqueueing
        lock_acquired = lock.acquire("in_progress")
        if not lock_acquired:
            job_id = lock.current_holder() or "in_progress"
        else:
            try:
                executive_summary, business_impact = "", ""
                remediations: list[dict[str, Any]] | None = None
                if payload.include_ai_narratives:
                    narrative = (
                        db.query(AINarrative)
                        .filter_by(project_id=project_id)
                        .order_by(AINarrative.generated_at.desc())
                        .first()
                    )
                    if narrative is not None:
                        executive_summary = narrative.executive_summary
                        business_impact = narrative.business_impact
                        remediations = list(narrative.remediation_priorities or [])

                watermark_text = "FREE TIER PREVIEW" if subscription.tier == "FREE" else None
                theme_options_dict = (
                    payload.theme_options.model_dump() if payload.theme_options else None
                )

                # F4-MED-13: pass finding_ids to respect client's selection
                job_id = enqueue(
                    workspace_id=str(workspace_id),
                    project_id=str(project_id),
                    report_title=project.name,
                    executive_summary=executive_summary,
                    business_impact=business_impact,
                    watermark_text=watermark_text,
                    finding_ids=payload.finding_ids,
                    theme_options=theme_options_dict,
                    remediations=remediations,
                )
                redis_client.set(f"lock:report:{project_id}", job_id, ex=LOCK_TTL_SECONDS)
                initial_job = {
                    "job_id": job_id,
                    "workspace_id": str(workspace_id),
                    "status": ReportJobStatus.QUEUED.value,
                    "progress_percentage": 10,
                    "report_id": None,
                    "error_message": None,
                }
                redis_client.set(
                    f"job:report:{job_id}",
                    json.dumps(initial_job),
                    ex=_JOB_STATUS_TTL_SECONDS,
                )
            except Exception:
                lock.release("in_progress")
                raise

    return CompilePDFAcceptedResponse(
        job_id=job_id,
        message="Report compilation has been queued.",
        status_url=f"/api/v1/workspaces/{workspace_id}/reports/jobs/{job_id}",
    )


@workspace_reports_router.get("/jobs/{job_id}", response_model=ReportJobStatusResponse)
def get_report_job_status(
    workspace_id: uuid.UUID,
    job_id: str,
    redis_client: Any = Depends(get_redis_client),
    _member: WorkspaceMember = Depends(_require_any_member),
) -> ReportJobStatusResponse:
    raw = redis_client.get(f"job:report:{job_id}")
    if not raw:
        raise ResourceNotFoundError("Report job not found.")

    try:
        data = json.loads(raw)
    except (TypeError, ValueError) as exc:
        raise ResourceNotFoundError("Report job not found.") from exc

    if data.get("workspace_id") != str(workspace_id):
        raise ResourceNotFoundError("Report job not found.")

    status = ReportJobStatus(str(data.get("status", ReportJobStatus.QUEUED.value)))
    report_id = data.get("report_id")

    if status == ReportJobStatus.COMPLETED and report_id:
        return ReportJobStatusResponse(
            job_id=job_id,
            status=status,
            progress_percentage=data.get("progress_percentage", 100),
            report_id=str(report_id),
            download_url=f"/api/v1/workspaces/{workspace_id}/reports/{report_id}/download",
            expires_in_seconds=PRESIGNED_URL_TTL_SECONDS,
        )

    if status == ReportJobStatus.FAILED:
        return ReportJobStatusResponse(
            job_id=job_id,
            status=status,
            progress_percentage=data.get("progress_percentage"),
            error_message=str(data.get("error_message") or "Report generation failed."),
        )

    return ReportJobStatusResponse(
        job_id=job_id,
        status=status,
        progress_percentage=data.get("progress_percentage", 10),
    )


@workspace_reports_router.get("/{report_id}/download", response_model=None)
def download_report(
    workspace_id: uuid.UUID,
    report_id: uuid.UUID,
    format: Annotated[Literal["redirect", "json"], Query()] = "redirect",
    db: Session = Depends(get_db),
    storage: S3StorageClient = Depends(get_report_storage),
    _member: WorkspaceMember = Depends(_require_any_member),
) -> RedirectResponse | ReportDownloadResponse:
    report = (
        db.query(Report)
        .join(Project, Project.id == Report.project_id)
        .filter(Report.id == report_id, Project.workspace_id == workspace_id)
        .one_or_none()
    )
    if report is None:
        raise ResourceNotFoundError("Report not found in this workspace.")

    presigned_url = storage.generate_presigned_url(
        report.storage_path, expires_in_seconds=PRESIGNED_URL_TTL_SECONDS
    )
    if format == "json":
        return ReportDownloadResponse(
            download_url=presigned_url,
            expires_in_seconds=PRESIGNED_URL_TTL_SECONDS,
        )
    return RedirectResponse(url=presigned_url, status_code=307)
