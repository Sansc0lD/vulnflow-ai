"""WorkspaceRouter — PLAN.md FASE 4.3 (SDD UC-03/UC-04/UC-05)."""

import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db, require_workspace_role
from app.core.exceptions import ResourceNotFoundError, ValidationFailedError
from app.core.security import (
    create_invitation_token,
    generate_api_key,
    get_jwt_algorithm,
    get_jwt_secret_key,
)
from app.models.api_key import APIKey
from app.models.subscription import Subscription
from app.models.user import User
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember
from vulnflow_contracts import (
    APIKeyCreateRequest,
    APIKeyCreateResponse,
    InviteMemberRequest,
    InviteMemberResponse,
    WorkspaceCreateRequest,
    WorkspaceResponse,
    WorkspaceUpdateRequest,
)

router = APIRouter(prefix="/api/v1/workspaces", tags=["workspaces"])

FREE_TIER_MONTHLY_REPORT_QUOTA = 3
MAX_WORKSPACES_PER_USER = 5
_INVITATION_EXPIRES_IN_SECONDS = 7 * 24 * 3600

_require_manager = require_workspace_role({"MANAGER"})


def _to_response(workspace: Workspace) -> WorkspaceResponse:
    return WorkspaceResponse(
        id=str(workspace.id),
        name=workspace.name,
        custom_logo_url=workspace.custom_logo_url,
        brand_primary_color=workspace.brand_primary_color,
        brand_secondary_color=workspace.brand_secondary_color,
        created_at=workspace.created_at,
    )


@router.post("", response_model=WorkspaceResponse, status_code=201)
def create_workspace(
    payload: WorkspaceCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WorkspaceResponse:
    # F4-LOW-15: limit workspace creation to prevent quota abuse
    manager_workspaces_count = (
        db.query(WorkspaceMember).filter_by(user_id=current_user.id, role="MANAGER").count()
    )
    if manager_workspaces_count >= MAX_WORKSPACES_PER_USER:
        raise ValidationFailedError(
            f"User cannot create more than {MAX_WORKSPACES_PER_USER} workspaces."
        )

    workspace = Workspace(name=payload.name)
    db.add(workspace)
    db.flush()
    db.add(WorkspaceMember(workspace_id=workspace.id, user_id=current_user.id, role="MANAGER"))
    db.add(
        Subscription(
            workspace_id=workspace.id,
            tier="FREE",
            monthly_report_quota=FREE_TIER_MONTHLY_REPORT_QUOTA,
            quota_reset_date=datetime.now(UTC) + timedelta(days=30),
        )
    )
    db.commit()
    return _to_response(workspace)


@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
def update_workspace(
    workspace_id: uuid.UUID,
    payload: WorkspaceUpdateRequest,
    db: Session = Depends(get_db),
    _member: WorkspaceMember = Depends(_require_manager),
) -> WorkspaceResponse:
    workspace = db.get(Workspace, workspace_id)
    if workspace is None:
        # _require_manager already proved a WorkspaceMember row exists for
        # this workspace_id, so this is unreachable in practice — but an
        # `assert` here would be stripped under `python -O` (Bandit B101),
        # so fail loudly with a real exception instead of a silent AttributeError.
        raise ResourceNotFoundError("Workspace not found.")

    for field in (
        "name",
        "custom_logo_url",
        "brand_primary_color",
        "brand_secondary_color",
        "confidentiality_text",
    ):
        value = getattr(payload, field)
        if value is not None:
            setattr(workspace, field, value)
    db.commit()
    return _to_response(workspace)


@router.post("/{workspace_id}/members", response_model=InviteMemberResponse, status_code=201)
def invite_member(
    workspace_id: uuid.UUID,
    payload: InviteMemberRequest,
    _member: WorkspaceMember = Depends(_require_manager),
) -> InviteMemberResponse:
    # F4-HIGH-11: Bind email to invitation token to prevent token reuse by arbitrary users
    token = create_invitation_token(
        workspace_id=str(workspace_id),
        email=str(payload.email),
        role=payload.role.value,
        secret_key=get_jwt_secret_key(),
        algorithm=get_jwt_algorithm(),
    )
    return InviteMemberResponse(invitation_token=token, expires_in=_INVITATION_EXPIRES_IN_SECONDS)


@router.post("/{workspace_id}/api-keys", response_model=APIKeyCreateResponse, status_code=201)
def create_api_key(
    workspace_id: uuid.UUID,
    payload: APIKeyCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _member: WorkspaceMember = Depends(_require_manager),
) -> APIKeyCreateResponse:
    raw_key, key_hash = generate_api_key()
    api_key = APIKey(
        workspace_id=workspace_id,
        created_by_user_id=current_user.id,
        key_hash=key_hash,
        label=payload.label,
    )
    db.add(api_key)
    db.commit()
    return APIKeyCreateResponse(id=str(api_key.id), label=api_key.label, api_key=raw_key)
