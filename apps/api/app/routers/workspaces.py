"""WorkspaceRouter — PLAN.md FASE 4.3 (SDD UC-03/UC-04/UC-05)."""

import contextlib
import os
import re
import time
import urllib.parse
import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt as pyjwt
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.audit import get_client_ip, record_audit_log
from app.core.dependencies import get_current_user, get_db, require_workspace_role
from app.core.exceptions import (
    AuthenticationError,
    ConflictError,
    PermissionDeniedError,
    ResourceNotFoundError,
    ValidationFailedError,
)
from app.core.security import (
    create_invitation_token,
    decode_invitation_token,
    generate_api_key,
    get_jwt_algorithm,
    get_jwt_secret_key,
    mark_invitation_used,
    verify_password,
)
from app.models.api_key import APIKey
from app.models.audit_log import AuditLog
from app.models.project import Project
from app.models.subscription import Subscription
from app.models.user import User
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember
from app.services.email_service import EmailSender, get_email_sender, send_invitation_email
from app.services.image_validator import validate_and_process_image
from app.services.s3_storage import (
    S3StorageClient,
    get_s3_bucket_name,
    make_boto_s3_client,
    make_public_boto_s3_client,
)
from vulnflow_contracts import (
    AcceptInvitationRequest,
    APIKeyCreateRequest,
    APIKeyCreateResponse,
    APIKeySummaryResponse,
    AuditLogEntryResponse,
    ImageUploadRequest,
    InviteMemberRequest,
    InviteMemberResponse,
    LogoUploadResponse,
    PaginatedAuditLogResponse,
    UpdateMemberRoleRequest,
    WorkspaceCreateRequest,
    WorkspaceDeleteRequest,
    WorkspaceMemberResponse,
    WorkspaceMembership,
    WorkspaceResponse,
    WorkspaceRole,
    WorkspaceUpdateRequest,
)

router = APIRouter(prefix="/api/v1/workspaces", tags=["workspaces"])

FREE_TIER_MONTHLY_REPORT_QUOTA = 3
MAX_WORKSPACES_PER_USER = 5
MAX_FREE_WORKSPACES_PER_USER = 1
MAX_ACTIVE_API_KEYS_PER_USER = 5
_INVITATION_EXPIRES_IN_SECONDS = 7 * 24 * 3600

_require_manager = require_workspace_role({"MANAGER"})
_require_key_creator = require_workspace_role({"MANAGER", "PENTESTER"})
_require_any_member = require_workspace_role({"MANAGER", "PENTESTER", "VIEWER"})


def get_upload_storage() -> S3StorageClient:
    return S3StorageClient(
        make_boto_s3_client(),
        bucket=get_s3_bucket_name(),
        public_client=make_public_boto_s3_client(),
    )


def _resolve_optional_storage(request: Request | None) -> S3StorageClient | None:
    if request is not None:
        override = request.app.dependency_overrides.get(get_upload_storage)
        if override is not None:
            return override()  # type: ignore[no-any-return]
    if not os.environ.get("S3_BUCKET_NAME"):
        return None
    try:
        return get_upload_storage()
    except Exception:
        return None


def _resolve_logo_display_url(
    workspace: Workspace, *, storage: S3StorageClient | None
) -> str | None:
    raw = workspace.custom_logo_url
    if not raw or raw.startswith("data:") or storage is None:
        return raw
    parsed_path = urllib.parse.urlsplit(raw).path
    match = re.search(
        rf"(workspaces/{re.escape(str(workspace.id))}/logo\.(?:png|jpg|jpeg|svg))$",
        parsed_path,
    )
    if match:
        with contextlib.suppress(Exception):
            return storage.generate_presigned_url(match.group(1), expires_in_seconds=900)
    return raw


def _to_response(
    workspace: Workspace, *, storage: S3StorageClient | None = None
) -> WorkspaceResponse:
    return WorkspaceResponse(
        id=str(workspace.id),
        name=workspace.name,
        custom_logo_url=_resolve_logo_display_url(workspace, storage=storage),
        brand_primary_color=workspace.brand_primary_color,
        brand_secondary_color=workspace.brand_secondary_color,
        confidentiality_text=workspace.confidentiality_text,
        created_at=workspace.created_at,
    )


@router.get("", response_model=list[WorkspaceResponse])
def list_workspaces(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[WorkspaceResponse]:
    workspaces = (
        db.query(Workspace)
        .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
        .filter(WorkspaceMember.user_id == current_user.id, Workspace.is_deleted.is_(False))
        .order_by(Workspace.created_at.desc())
        .all()
    )
    storage = _resolve_optional_storage(request)
    return [_to_response(ws, storage=storage) for ws in workspaces]


@router.post("/invitations/accept", response_model=WorkspaceMembership)
def accept_invitation(
    payload: AcceptInvitationRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WorkspaceMembership:
    try:
        invite = decode_invitation_token(
            payload.invitation_token,
            secret_key=get_jwt_secret_key(),
            algorithm=get_jwt_algorithm(),
        )
    except pyjwt.InvalidTokenError as exc:
        raise AuthenticationError("Invitation token is invalid or expired.") from exc

    token_email = str(invite.get("email", ""))
    if token_email and token_email.lower() != current_user.email.lower():
        raise AuthenticationError("Invitation token was issued for a different email address.")

    try:
        workspace_uuid = uuid.UUID(str(invite["workspace_id"]))
    except (KeyError, ValueError) as exc:
        raise AuthenticationError("Invitation token payload is malformed.") from exc

    workspace = db.get(Workspace, workspace_uuid)
    if workspace is None or workspace.is_deleted:
        raise ResourceNotFoundError("The invited workspace no longer exists.")

    existing = (
        db.query(WorkspaceMember)
        .filter_by(workspace_id=workspace.id, user_id=current_user.id)
        .one_or_none()
    )
    if existing is not None:
        raise ConflictError("You are already a member of this workspace.")

    role = str(invite["role"])
    db.add(WorkspaceMember(workspace_id=workspace.id, user_id=current_user.id, role=role))
    record_audit_log(
        db,
        workspace_id=workspace.id,
        actor_user_id=current_user.id,
        action="INVITATION_ACCEPTED",
        target_entity=f"user:{current_user.id}",
        ip_address=get_client_ip(request),
        details={"role": role},
    )
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError("You are already a member of this workspace.") from exc

    jti = invite.get("jti")
    if jti:
        exp = int(invite.get("exp", int(time.time()) + _INVITATION_EXPIRES_IN_SECONDS))
        mark_invitation_used(str(jti), exp)

    sub = db.query(Subscription).filter_by(workspace_id=workspace.id).one_or_none()
    return WorkspaceMembership(
        id=str(workspace.id),
        name=workspace.name,
        role=WorkspaceRole(role),
        tier=sub.tier if sub is not None else None,
    )


@router.post("", response_model=WorkspaceResponse, status_code=201)
def create_workspace(
    payload: WorkspaceCreateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WorkspaceResponse:
    # Enforce max 1 owned FREE workspace per user (upgrade existing workspaces to unlock more).
    free_manager_workspaces_count = (
        db.query(WorkspaceMember)
        .join(Workspace, Workspace.id == WorkspaceMember.workspace_id)
        .join(Subscription, Subscription.workspace_id == Workspace.id)
        .filter(
            WorkspaceMember.user_id == current_user.id,
            WorkspaceMember.role == "MANAGER",
            Workspace.is_deleted.is_(False),
            Subscription.tier == "FREE",
        )
        .count()
    )
    if free_manager_workspaces_count >= MAX_FREE_WORKSPACES_PER_USER:
        raise ValidationFailedError(
            "You already own a Free-tier workspace. Upgrade an existing workspace "
            "to Pro or Enterprise before creating another."
        )

    # F4-LOW-15: limit total owned workspaces to prevent quota abuse
    manager_workspaces_count = (
        db.query(WorkspaceMember)
        .join(Workspace, Workspace.id == WorkspaceMember.workspace_id)
        .filter(
            WorkspaceMember.user_id == current_user.id,
            WorkspaceMember.role == "MANAGER",
            Workspace.is_deleted.is_(False),
        )
        .count()
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
    record_audit_log(
        db,
        workspace_id=workspace.id,
        actor_user_id=current_user.id,
        action="WORKSPACE_CREATED",
        target_entity=f"workspace:{workspace.id}",
        ip_address=get_client_ip(request),
        details={"name": workspace.name},
    )
    db.commit()
    return _to_response(workspace, storage=_resolve_optional_storage(request))


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
def get_workspace(
    workspace_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    _member: WorkspaceMember = Depends(_require_any_member),
) -> WorkspaceResponse:
    workspace = db.get(Workspace, workspace_id)
    if workspace is None or workspace.is_deleted:
        raise ResourceNotFoundError("Workspace not found.")
    return _to_response(workspace, storage=_resolve_optional_storage(request))


@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
def update_workspace(
    workspace_id: uuid.UUID,
    payload: WorkspaceUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_member: WorkspaceMember = Depends(_require_manager),
) -> WorkspaceResponse:
    workspace = db.get(Workspace, workspace_id)
    if workspace is None or workspace.is_deleted:
        raise ResourceNotFoundError("Workspace not found.")

    updated_fields: list[str] = []
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
            updated_fields.append(field)

    record_audit_log(
        db,
        workspace_id=workspace.id,
        actor_user_id=current_member.user_id,
        action="WORKSPACE_UPDATED",
        target_entity=f"workspace:{workspace.id}",
        ip_address=get_client_ip(request),
        details={"updated_fields": updated_fields},
    )
    db.commit()
    return _to_response(workspace, storage=_resolve_optional_storage(request))


@router.delete("/{workspace_id}")
def delete_workspace(
    workspace_id: uuid.UUID,
    payload: WorkspaceDeleteRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _member: WorkspaceMember = Depends(_require_manager),
) -> dict[str, str]:
    workspace = db.get(Workspace, workspace_id)
    if workspace is None or workspace.is_deleted:
        raise ResourceNotFoundError("Workspace not found.")
    if not verify_password(payload.password, current_user.password_hash):
        raise AuthenticationError("Invalid password.")
    if payload.confirm_workspace_name != workspace.name:
        raise ValidationFailedError("Confirmation workspace name does not match.")

    active_projects = (
        db.query(Project).filter_by(workspace_id=workspace_id, status="ACTIVE").count()
    )
    if active_projects > 0:
        raise ConflictError(
            "Cannot delete workspace while active projects exist; archive projects first."
        )

    workspace.is_deleted = True
    record_audit_log(
        db,
        workspace_id=workspace.id,
        actor_user_id=current_user.id,
        action="WORKSPACE_DELETED",
        target_entity=f"workspace:{workspace.id}",
        ip_address=get_client_ip(request),
        details={"name": workspace.name},
    )
    db.commit()
    return {"status": "DELETED"}


@router.get("/{workspace_id}/members", response_model=list[WorkspaceMemberResponse])
def list_workspace_members(
    workspace_id: uuid.UUID,
    db: Session = Depends(get_db),
    _member: WorkspaceMember = Depends(_require_any_member),
) -> list[WorkspaceMemberResponse]:
    rows = (
        db.query(WorkspaceMember, User)
        .join(User, User.id == WorkspaceMember.user_id)
        .filter(WorkspaceMember.workspace_id == workspace_id)
        .order_by(User.email.asc())
        .all()
    )
    return [
        WorkspaceMemberResponse(
            user_id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            role=WorkspaceRole(member.role),
        )
        for member, user in rows
    ]


@router.post("/{workspace_id}/members", response_model=InviteMemberResponse, status_code=201)
def invite_member(
    workspace_id: uuid.UUID,
    payload: InviteMemberRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    email_sender: EmailSender = Depends(get_email_sender),
    _member: WorkspaceMember = Depends(_require_manager),
) -> InviteMemberResponse:
    workspace = db.get(Workspace, workspace_id)
    if workspace is None or workspace.is_deleted:
        raise ResourceNotFoundError("Workspace not found.")

    # F4-HIGH-11: Bind email to invitation token to prevent token reuse by arbitrary users
    token = create_invitation_token(
        workspace_id=str(workspace_id),
        email=str(payload.email),
        role=payload.role.value,
        secret_key=get_jwt_secret_key(),
        algorithm=get_jwt_algorithm(),
    )
    send_invitation_email(
        email_sender,
        to_email=str(payload.email),
        workspace_name=workspace.name,
        role=payload.role.value,
        invitation_token=token,
    )
    record_audit_log(
        db,
        workspace_id=workspace_id,
        actor_user_id=current_user.id,
        action="MEMBER_INVITED",
        target_entity=f"invitation:{payload.email}",
        ip_address=get_client_ip(request),
        details={"email": str(payload.email), "role": payload.role.value},
    )
    db.commit()
    return InviteMemberResponse(invitation_token=token, expires_in=_INVITATION_EXPIRES_IN_SECONDS)


@router.patch("/{workspace_id}/members/{target_user_id}", response_model=WorkspaceMemberResponse)
def update_member_role(
    workspace_id: uuid.UUID,
    target_user_id: uuid.UUID,
    payload: UpdateMemberRoleRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_member: WorkspaceMember = Depends(_require_manager),
) -> WorkspaceMemberResponse:
    row = (
        db.query(WorkspaceMember, User)
        .join(User, User.id == WorkspaceMember.user_id)
        .filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == target_user_id,
        )
        .one_or_none()
    )
    if row is None:
        raise ResourceNotFoundError("Workspace member not found.")
    target_member, target_user = row

    if target_member.role == "MANAGER" and payload.role != WorkspaceRole.MANAGER:
        other_managers = (
            db.query(WorkspaceMember)
            .filter(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.role == "MANAGER",
                WorkspaceMember.user_id != target_user_id,
            )
            .count()
        )
        if other_managers == 0:
            raise ConflictError("Workspace must retain at least one MANAGER.")

    old_role = target_member.role
    target_member.role = payload.role.value
    if payload.role == WorkspaceRole.VIEWER:
        db.query(APIKey).filter(
            APIKey.workspace_id == workspace_id,
            APIKey.created_by_user_id == target_user_id,
            APIKey.is_active.is_(True),
        ).update({"is_active": False}, synchronize_session=False)
    record_audit_log(
        db,
        workspace_id=workspace_id,
        actor_user_id=current_member.user_id,
        action="MEMBER_ROLE_UPDATED",
        target_entity=f"user:{target_user_id}",
        ip_address=get_client_ip(request),
        details={"old_role": old_role, "new_role": payload.role.value},
    )
    db.commit()
    return WorkspaceMemberResponse(
        user_id=str(target_user.id),
        email=target_user.email,
        full_name=target_user.full_name,
        role=payload.role,
    )


@router.delete("/{workspace_id}/members/{target_user_id}")
def remove_workspace_member(
    workspace_id: uuid.UUID,
    target_user_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_member: WorkspaceMember = Depends(_require_manager),
) -> dict[str, str]:
    target_member = (
        db.query(WorkspaceMember)
        .filter_by(workspace_id=workspace_id, user_id=target_user_id)
        .one_or_none()
    )
    if target_member is None:
        raise ResourceNotFoundError("Workspace member not found.")

    if target_member.role == "MANAGER":
        other_managers = (
            db.query(WorkspaceMember)
            .filter(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.role == "MANAGER",
                WorkspaceMember.user_id != target_user_id,
            )
            .count()
        )
        if other_managers == 0:
            raise ConflictError("Cannot remove the sole MANAGER from the workspace.")

    removed_role = target_member.role
    db.query(APIKey).filter(
        APIKey.workspace_id == workspace_id,
        APIKey.created_by_user_id == target_user_id,
        APIKey.is_active.is_(True),
    ).update({"is_active": False}, synchronize_session=False)
    db.delete(target_member)
    record_audit_log(
        db,
        workspace_id=workspace_id,
        actor_user_id=current_member.user_id,
        action="MEMBER_REMOVED",
        target_entity=f"user:{target_user_id}",
        ip_address=get_client_ip(request),
        details={"removed_role": removed_role},
    )
    db.commit()
    return {"status": "REMOVED"}


@router.post("/{workspace_id}/api-keys", response_model=APIKeyCreateResponse, status_code=201)
def create_api_key(
    workspace_id: uuid.UUID,
    payload: APIKeyCreateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _member: WorkspaceMember = Depends(_require_key_creator),
) -> APIKeyCreateResponse:
    active_count = (
        db.query(APIKey)
        .filter_by(
            workspace_id=workspace_id,
            created_by_user_id=current_user.id,
            is_active=True,
        )
        .count()
    )
    if active_count >= MAX_ACTIVE_API_KEYS_PER_USER:
        raise ValidationFailedError(
            f"Maximum of {MAX_ACTIVE_API_KEYS_PER_USER} active API keys per user reached."
        )

    raw_key, key_hash = generate_api_key()
    api_key = APIKey(
        workspace_id=workspace_id,
        created_by_user_id=current_user.id,
        key_hash=key_hash,
        label=payload.label,
    )
    db.add(api_key)
    db.flush()
    record_audit_log(
        db,
        workspace_id=workspace_id,
        actor_user_id=current_user.id,
        action="API_KEY_CREATED",
        target_entity=f"api_key:{api_key.id}",
        ip_address=get_client_ip(request),
        details={"label": api_key.label},
    )
    db.commit()
    return APIKeyCreateResponse(id=str(api_key.id), label=api_key.label, api_key=raw_key)


@router.get("/{workspace_id}/api-keys", response_model=list[APIKeySummaryResponse])
def list_api_keys(
    workspace_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_member: WorkspaceMember = Depends(_require_key_creator),
) -> list[APIKeySummaryResponse]:
    query = db.query(APIKey).filter(APIKey.workspace_id == workspace_id)
    if current_member.role != "MANAGER":
        query = query.filter(APIKey.created_by_user_id == current_member.user_id)
    keys = query.order_by(APIKey.is_active.desc(), APIKey.label.asc()).all()
    return [
        APIKeySummaryResponse(
            id=str(k.id),
            label=k.label,
            is_active=k.is_active,
            last_used_at=k.last_used_at,
            created_by_user_id=str(k.created_by_user_id),
        )
        for k in keys
    ]


@router.delete("/{workspace_id}/api-keys/{key_id}")
def revoke_api_key(
    workspace_id: uuid.UUID,
    key_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_member: WorkspaceMember = Depends(_require_key_creator),
) -> dict[str, str]:
    api_key = db.query(APIKey).filter_by(id=key_id, workspace_id=workspace_id).one_or_none()
    if api_key is None:
        raise ResourceNotFoundError("API key not found in this workspace.")
    if current_member.role != "MANAGER" and api_key.created_by_user_id != current_member.user_id:
        raise PermissionDeniedError("You can only revoke API keys you created.")

    api_key.is_active = False
    record_audit_log(
        db,
        workspace_id=workspace_id,
        actor_user_id=current_member.user_id,
        action="API_KEY_REVOKED",
        target_entity=f"api_key:{api_key.id}",
        ip_address=get_client_ip(request),
        details={"label": api_key.label},
    )
    db.commit()
    return {"status": "REVOKED"}


@router.post("/{workspace_id}/logo", response_model=LogoUploadResponse)
def upload_workspace_logo(
    workspace_id: uuid.UUID,
    payload: ImageUploadRequest,
    request: Request,
    db: Session = Depends(get_db),
    storage: S3StorageClient = Depends(get_upload_storage),
    current_member: WorkspaceMember = Depends(_require_manager),
) -> LogoUploadResponse:
    workspace = db.get(Workspace, workspace_id)
    if workspace is None or workspace.is_deleted:
        raise ResourceNotFoundError("Workspace not found.")

    subscription = db.query(Subscription).filter_by(workspace_id=workspace_id).one_or_none()
    if subscription is None or subscription.tier not in {"PRO", "ENTERPRISE"}:
        raise PermissionDeniedError("Custom workspace logo requires a PRO or ENTERPRISE plan.")

    image_bytes, resolved_ct, ext = validate_and_process_image(
        data_base64=payload.data_base64,
        content_type=payload.content_type,
        max_bytes=2 * 1024 * 1024,
        allow_svg=True,
    )
    storage_path = f"workspaces/{workspace_id}/logo.{ext}"
    storage.upload_bytes(storage_path, image_bytes, content_type=resolved_ct)
    logo_url = storage.generate_presigned_url(storage_path, expires_in_seconds=604800)

    # Store durable object key rather than a truncated/expiring presigned URL.
    workspace.custom_logo_url = storage_path
    record_audit_log(
        db,
        workspace_id=workspace_id,
        actor_user_id=current_member.user_id,
        action="WORKSPACE_LOGO_UPLOADED",
        target_entity=f"workspace:{workspace_id}",
        ip_address=get_client_ip(request),
        details={"storage_path": storage_path, "content_type": resolved_ct},
    )
    db.commit()
    return LogoUploadResponse(custom_logo_url=logo_url, storage_path=storage_path)


@router.get("/{workspace_id}/audit-logs", response_model=PaginatedAuditLogResponse)
def list_workspace_audit_logs(
    workspace_id: uuid.UUID,
    action: Annotated[str | None, Query()] = None,
    actor_user_id: Annotated[uuid.UUID | None, Query()] = None,
    date_from: Annotated[datetime | None, Query()] = None,
    date_to: Annotated[datetime | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    db: Session = Depends(get_db),
    _member: WorkspaceMember = Depends(_require_manager),
) -> PaginatedAuditLogResponse:
    query = db.query(AuditLog).filter(AuditLog.workspace_id == workspace_id)
    if action is not None:
        query = query.filter(AuditLog.action == action)
    if actor_user_id is not None:
        query = query.filter(AuditLog.actor_user_id == actor_user_id)
    if date_from is not None:
        query = query.filter(AuditLog.created_at >= date_from)
    if date_to is not None:
        query = query.filter(AuditLog.created_at <= date_to)

    total = int(query.count())
    entries = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()
    return PaginatedAuditLogResponse(
        items=[
            AuditLogEntryResponse(
                id=str(entry.id),
                created_at=entry.created_at,
                workspace_id=str(entry.workspace_id),
                actor_user_id=str(entry.actor_user_id) if entry.actor_user_id else None,
                action=entry.action,
                target_entity=entry.target_entity,
                ip_address=entry.ip_address,
                details=entry.details or {},
            )
            for entry in entries
        ],
        total=total,
        limit=limit,
        offset=offset,
    )
