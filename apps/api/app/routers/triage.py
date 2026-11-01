"""TriageRouter — PLAN.md FASE 4.5 (SDD UC-09; EC-11 optimistic locking; EC-12)."""

import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError

from app.core.dependencies import get_db, require_workspace_role
from app.core.exceptions import ConflictError, ResourceNotFoundError
from app.models.audit_log import AuditLog
from app.models.finding import Finding
from app.models.project import Project
from app.models.workspace_member import WorkspaceMember
from vulnflow_contracts import FindingStatusResponse, UpdateFindingStatusRequest

router = APIRouter(
    prefix="/api/v1/workspaces/{workspace_id}/projects/{project_id}/findings", tags=["triage"]
)

_require_triager_role = require_workspace_role({"MANAGER", "PENTESTER"})


@router.patch("/{finding_id}/status", response_model=FindingStatusResponse)
def update_finding_status(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    finding_id: uuid.UUID,
    payload: UpdateFindingStatusRequest,
    request: Request,
    current_member: WorkspaceMember = Depends(_require_triager_role),
    db: Session = Depends(get_db),
) -> FindingStatusResponse:
    # F4-CRIT-01: Verify that project belongs to this workspace
    project = db.query(Project).filter_by(id=project_id, workspace_id=workspace_id).one_or_none()
    if project is None:
        raise ResourceNotFoundError("Project not found in this workspace.")

    finding = db.query(Finding).filter_by(id=finding_id, project_id=project_id).one_or_none()
    if finding is None:
        raise ResourceNotFoundError("Finding not found in this project.")

    if finding.version != payload.version:
        raise ConflictError(
            "This finding was modified by another request; reload and retry (EC-11)."
        )

    old_status = finding.status
    finding.status = payload.status.value
    # `version` is NOT incremented here: `Finding.__mapper_args__` registers it
    # as SQLAlchemy's `version_id_col`, so the UPDATE carries
    # `WHERE version = :old_version` and the bump happens as part of that
    # statement. Incrementing by hand would double-count it.
    # EC-12: a finding marked FALSE_POSITIVE must never stay curated for
    # the compiled report, regardless of what the client sent.
    if payload.status.value == "FALSE_POSITIVE":
        finding.is_curated_for_report = False

    db.add(
        AuditLog(
            workspace_id=workspace_id,
            actor_user_id=current_member.user_id,
            action="FINDING_STATUS_CHANGE",
            target_entity="findings",
            ip_address=request.client.host if request.client else "unknown",
            details={
                "finding_id": str(finding_id),
                "old_status": old_status,
                "new_status": finding.status,
            },
        )
    )
    try:
        db.commit()
    except StaleDataError as exc:
        # The `payload.version` check above is only a fast path; it cannot stop
        # a true race, because two requests can both read version=1 before
        # either writes. This is the authoritative guard: the UPDATE matched 0
        # rows, meaning a concurrent transaction committed first (EC-11).
        db.rollback()
        raise ConflictError(
            "This finding was modified by another request; reload and retry (EC-11)."
        ) from exc

    return FindingStatusResponse(
        id=str(finding.id),
        status=payload.status,
        version=finding.version,
        is_curated_for_report=finding.is_curated_for_report,
    )
