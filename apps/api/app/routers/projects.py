"""ProjectRouter — PLAN.md FASE 4.3 (SDD UC-06/UC-06a; EC-05 ROE timezone handling)."""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_workspace_role
from app.core.exceptions import ResourceNotFoundError, ValidationFailedError
from app.models.project import Project
from app.models.workspace_member import WorkspaceMember
from vulnflow_contracts import AssignLeadRequest, ProjectCreateRequest, ProjectResponse

router = APIRouter(prefix="/api/v1/workspaces/{workspace_id}/projects", tags=["projects"])

_require_creator_role = require_workspace_role({"MANAGER", "PENTESTER"})
_require_any_member = require_workspace_role({"MANAGER", "PENTESTER", "VIEWER"})
_require_manager = require_workspace_role({"MANAGER"})

_SCOPE_SEPARATOR = "\n"


def _to_response(project: Project) -> ProjectResponse:
    return ProjectResponse(
        id=str(project.id),
        workspace_id=str(project.workspace_id),
        name=project.name,
        client_name=project.client_name,
        target_scope=project.target_scope.split(_SCOPE_SEPARATOR),
        roe_start_date=project.roe_start_date,
        roe_end_date=project.roe_end_date,
        timezone=project.timezone,
        status=project.status,
        lead_pentester_id=str(project.lead_pentester_id) if project.lead_pentester_id else None,
    )


@router.post("", response_model=ProjectResponse, status_code=201)
def create_project(
    workspace_id: uuid.UUID,
    payload: ProjectCreateRequest,
    db: Session = Depends(get_db),
    _member: WorkspaceMember = Depends(_require_creator_role),
) -> ProjectResponse:
    # F4-LOW-23: sanitize scope entries to ensure embedded newlines do not split entries
    sanitized_scope = [
        entry.strip().replace("\r", "").replace("\n", "")
        for entry in payload.target_scope
        if entry.strip()
    ]
    if not sanitized_scope:
        raise ValidationFailedError("target_scope must contain at least one non-empty entry.")

    project = Project(
        workspace_id=workspace_id,
        name=payload.name,
        client_name=payload.client_name,
        target_scope=_SCOPE_SEPARATOR.join(sanitized_scope),
        roe_start_date=payload.roe_start_date,
        roe_end_date=payload.roe_end_date,
        timezone=payload.timezone,
    )
    db.add(project)
    db.commit()
    return _to_response(project)


@router.get("", response_model=list[ProjectResponse])
def list_projects(
    workspace_id: uuid.UUID,
    db: Session = Depends(get_db),
    _member: WorkspaceMember = Depends(_require_any_member),
) -> list[ProjectResponse]:
    projects = db.query(Project).filter_by(workspace_id=workspace_id).all()
    return [_to_response(project) for project in projects]


@router.patch("/{project_id}/lead", response_model=ProjectResponse)
def assign_lead_pentester(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    payload: AssignLeadRequest,
    db: Session = Depends(get_db),
    _member: WorkspaceMember = Depends(_require_manager),
) -> ProjectResponse:
    project = db.query(Project).filter_by(id=project_id, workspace_id=workspace_id).one_or_none()
    if project is None:
        raise ResourceNotFoundError("Project not found in this workspace.")

    # F4-MED-16: Catch invalid UUID format from client input
    try:
        lead_user_id = uuid.UUID(payload.lead_pentester_id)
    except ValueError as exc:
        raise ValidationFailedError(f"Invalid UUID for lead_pentester_id: {exc}") from exc

    # F4-HIGH-12: verify assignee is a member of this workspace (prevent IDOR)
    assignee_member = (
        db.query(WorkspaceMember)
        .filter_by(workspace_id=workspace_id, user_id=lead_user_id)
        .one_or_none()
    )
    if assignee_member is None:
        raise ResourceNotFoundError("Assignee is not a member of this workspace.")

    project.lead_pentester_id = lead_user_id
    db.commit()
    return _to_response(project)
