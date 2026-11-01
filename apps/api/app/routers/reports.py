"""ReportRouter — PLAN.md FASE 4.7 (SDD §2.6.1.5; EC-15/EC-16/EC-17)."""

import uuid
from typing import Any, Protocol

from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_workspace_role
from app.core.exceptions import ResourceNotFoundError
from app.core.redis_client import DistributedLock, get_redis_client
from app.models.ai_narrative import AINarrative
from app.models.project import Project
from app.models.report import Report
from app.models.subscription import Subscription
from app.models.workspace_member import WorkspaceMember
from app.services.s3_storage import S3StorageClient, get_s3_bucket_name, make_boto_s3_client
from vulnflow_contracts import CompilePDFAcceptedResponse, CompilePDFRequest

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


class ReportEnqueuer(Protocol):
    def __call__(self, **kwargs: Any) -> str: ...


def get_report_storage() -> S3StorageClient:
    """Default (production) storage client — overridden in tests."""
    return S3StorageClient(make_boto_s3_client(), bucket=get_s3_bucket_name())


def get_report_enqueuer() -> ReportEnqueuer:
    """Default (production) enqueuer — hands off to the real Celery task.
    Overridden in tests so no live Redis broker is required."""
    from app.workers.report_worker import compile_pdf_task

    def _enqueue(**kwargs: Any) -> str:
        result: Any = compile_pdf_task.delay(**kwargs)
        return str(result.id)

    return _enqueue


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

                subscription = (
                    db.query(Subscription).filter_by(workspace_id=workspace_id).one_or_none()
                )
                watermark_text = (
                    "FREE TIER PREVIEW" if subscription and subscription.tier == "FREE" else None
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
                )
                redis_client.set(f"lock:report:{project_id}", job_id, ex=LOCK_TTL_SECONDS)
            except Exception:
                lock.release("in_progress")
                raise

    return CompilePDFAcceptedResponse(
        job_id=job_id,
        message="Report compilation has been queued.",
        status_url=f"/api/v1/workspaces/{workspace_id}/reports/jobs/{job_id}",
    )


@workspace_reports_router.get("/{report_id}/download")
def download_report(
    workspace_id: uuid.UUID,
    report_id: uuid.UUID,
    db: Session = Depends(get_db),
    storage: S3StorageClient = Depends(get_report_storage),
    _member: WorkspaceMember = Depends(_require_any_member),
) -> RedirectResponse:
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
    return RedirectResponse(url=presigned_url, status_code=307)
