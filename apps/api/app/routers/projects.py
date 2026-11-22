"""ProjectRouter — PLAN.md FASE 4.3 (SDD UC-06/UC-06a; EC-05 ROE timezone handling)."""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.audit import get_client_ip, record_audit_log
from app.core.dependencies import get_db, require_workspace_role
from app.core.exceptions import ResourceNotFoundError, ValidationFailedError
from app.models.project import Project
from app.models.workspace_member import WorkspaceMember
from vulnflow_contracts import (
    AssignLeadRequest,
    ProjectCreateRequest,
    ProjectResponse,
    ProjectTechStack,
    ProjectUpdateRequest,
)

router = APIRouter(prefix="/api/v1/workspaces/{workspace_id}/projects", tags=["projects"])

_require_creator_role = require_workspace_role({"MANAGER", "PENTESTER"})
_require_any_member = require_workspace_role({"MANAGER", "PENTESTER", "VIEWER"})
_require_manager = require_workspace_role({"MANAGER"})

_SCOPE_SEPARATOR = "\n"


def _normalize_utc(dt: datetime) -> datetime:
    return dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt


def _sanitize_scope_entries(entries: list[str]) -> list[str]:
    # F4-LOW-23: sanitize scope entries to ensure embedded newlines do not split entries
    sanitized = [
        entry.strip().replace("\r", "").replace("\n", "") for entry in entries if entry.strip()
    ]
    if not sanitized:
        raise ValidationFailedError("target_scope must contain at least one non-empty entry.")
    return sanitized


def _to_response(project: Project) -> ProjectResponse:
    stack_obj = (
        ProjectTechStack.model_validate(project.tech_stack)
        if isinstance(project.tech_stack, dict) and project.tech_stack
        else None
    )
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
        tech_stack=stack_obj,
    )


@router.post("", response_model=ProjectResponse, status_code=201)
def create_project(
    workspace_id: uuid.UUID,
    payload: ProjectCreateRequest,
    db: Session = Depends(get_db),
    _member: WorkspaceMember = Depends(_require_creator_role),
) -> ProjectResponse:
    sanitized_scope = _sanitize_scope_entries(payload.target_scope)
    stack_dict = (
        payload.tech_stack.model_dump(exclude_none=True) if payload.tech_stack is not None else None
    )

    project = Project(
        workspace_id=workspace_id,
        name=payload.name,
        client_name=payload.client_name,
        target_scope=_SCOPE_SEPARATOR.join(sanitized_scope),
        roe_start_date=payload.roe_start_date,
        roe_end_date=payload.roe_end_date,
        timezone=payload.timezone,
        tech_stack=stack_dict or None,
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


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    _member: WorkspaceMember = Depends(_require_any_member),
) -> ProjectResponse:
    project = db.query(Project).filter_by(id=project_id, workspace_id=workspace_id).one_or_none()
    if project is None:
        raise ResourceNotFoundError("Project not found in this workspace.")
    return _to_response(project)


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    payload: ProjectUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_member: WorkspaceMember = Depends(_require_creator_role),
) -> ProjectResponse:
    project = db.query(Project).filter_by(id=project_id, workspace_id=workspace_id).one_or_none()
    if project is None:
        raise ResourceNotFoundError("Project not found in this workspace.")

    new_start = _normalize_utc(payload.roe_start_date or project.roe_start_date)
    new_end = _normalize_utc(payload.roe_end_date or project.roe_end_date)
    if new_end <= new_start:
        raise ValidationFailedError("roe_end_date must be after roe_start_date.")

    updated_fields: list[str] = []
    if payload.name is not None:
        project.name = payload.name
        updated_fields.append("name")
    if payload.client_name is not None:
        project.client_name = payload.client_name
        updated_fields.append("client_name")
    if payload.target_scope is not None:
        project.target_scope = _SCOPE_SEPARATOR.join(_sanitize_scope_entries(payload.target_scope))
        updated_fields.append("target_scope")
    if payload.roe_start_date is not None:
        project.roe_start_date = payload.roe_start_date
        updated_fields.append("roe_start_date")
    if payload.roe_end_date is not None:
        project.roe_end_date = payload.roe_end_date
        updated_fields.append("roe_end_date")
    if payload.timezone is not None:
        project.timezone = payload.timezone
        updated_fields.append("timezone")
    if payload.status is not None:
        project.status = payload.status
        updated_fields.append("status")
    if payload.tech_stack is not None:
        stack_dict = payload.tech_stack.model_dump(exclude_none=True)
        project.tech_stack = stack_dict or None
        updated_fields.append("tech_stack")

    record_audit_log(
        db,
        workspace_id=workspace_id,
        actor_user_id=current_member.user_id,
        action="PROJECT_UPDATED",
        target_entity=f"project:{project.id}",
        ip_address=get_client_ip(request),
        details={"updated_fields": updated_fields, "status": project.status},
    )
    db.commit()
    return _to_response(project)


@router.patch("/{project_id}/lead", response_model=ProjectResponse)
def assign_lead_pentester(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    payload: AssignLeadRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_member: WorkspaceMember = Depends(_require_manager),
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
    if assignee_member.role == "VIEWER":
        raise ValidationFailedError("VIEWER cannot be assigned as lead pentester.")

    project.lead_pentester_id = lead_user_id
    record_audit_log(
        db,
        workspace_id=workspace_id,
        actor_user_id=current_member.user_id,
        action="PROJECT_LEAD_ASSIGNED",
        target_entity=f"project:{project.id}",
        ip_address=get_client_ip(request),
        details={"lead_pentester_id": str(lead_user_id)},
    )
    db.commit()
    return _to_response(project)
