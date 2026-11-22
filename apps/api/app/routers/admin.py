"""Superadmin telemetry, user governance, and audit log endpoints — UC-17..19."""

import uuid
from datetime import UTC, datetime
from typing import Annotated, Any, cast

from fastapi import APIRouter, Depends, Query, Request
from redis.exceptions import RedisError
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.audit import SYSTEM_WORKSPACE_ID, get_client_ip, record_audit_log
from app.core.dependencies import get_db, require_superadmin
from app.core.exceptions import ResourceNotFoundError, ValidationFailedError
from app.core.redis_client import get_optional_redis_client
from app.domain.telemetry import (
    compute_ai_telemetry,
    get_monthly_spend_ceiling_usd,
    set_monthly_spend_ceiling_usd,
)
from app.models.api_key import APIKey
from app.models.audit_log import AuditLog
from app.models.enterprise_inquiry import EnterpriseInquiry
from app.models.subscription import Subscription
from app.models.user import User
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember
from vulnflow_contracts import (
    AdminSubscriptionOverrideRequest,
    AdminUserSummary,
    AdminWorkspaceSubscriptionSummary,
    AITelemetryResponse,
    AuditLogEntryResponse,
    EnterpriseInquiryResponse,
    EnterpriseInquiryStatus,
    EnterpriseInquiryUpdateRequest,
    PaginatedAuditLogResponse,
    SpendCeilingUpdateRequest,
    SuspendUserRequest,
)

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


def _safe_read_spend_ceiling(redis_client: Any) -> float:
    try:
        return get_monthly_spend_ceiling_usd(redis_client)
    except (RedisError, OSError):
        return get_monthly_spend_ceiling_usd(None)


def _user_workspace_count(db: Session, user_id: uuid.UUID) -> int:
    return int(
        db.query(func.count(WorkspaceMember.id))
        .join(Workspace, Workspace.id == WorkspaceMember.workspace_id)
        .filter(WorkspaceMember.user_id == user_id, Workspace.is_deleted.is_(False))
        .scalar()
        or 0
    )


def _to_user_summary(user: User, workspace_count: int) -> AdminUserSummary:
    return AdminUserSummary(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        status=user.status,
        is_superadmin=user.is_superadmin,
        mfa_enabled=bool(user.totp_secret),
        created_at=user.created_at,
        workspace_count=workspace_count,
    )


@router.get("/telemetry/ai", response_model=AITelemetryResponse)
def get_ai_telemetry(
    _admin: User = Depends(require_superadmin),
    db: Session = Depends(get_db),
    redis_client: Any | None = Depends(get_optional_redis_client),
) -> AITelemetryResponse:
    ceiling = _safe_read_spend_ceiling(redis_client)
    return compute_ai_telemetry(db, spend_ceiling_usd=ceiling)


@router.patch("/telemetry/ai/ceiling", response_model=AITelemetryResponse)
def update_ai_spend_ceiling(
    payload: SpendCeilingUpdateRequest,
    request: Request,
    admin_user: User = Depends(require_superadmin),
    db: Session = Depends(get_db),
    redis_client: Any | None = Depends(get_optional_redis_client),
) -> AITelemetryResponse:
    if redis_client is None:
        raise ValidationFailedError("Redis is not configured for spend ceiling updates.")
    set_monthly_spend_ceiling_usd(redis_client, payload.monthly_spend_ceiling_usd)
    record_audit_log(
        db,
        workspace_id=SYSTEM_WORKSPACE_ID,
        actor_user_id=admin_user.id,
        action="AI_SPEND_CEILING_UPDATED",
        target_entity="system:ai_telemetry",
        ip_address=get_client_ip(request),
        details={"monthly_spend_ceiling_usd": payload.monthly_spend_ceiling_usd},
    )
    db.commit()
    return compute_ai_telemetry(db, spend_ceiling_usd=payload.monthly_spend_ceiling_usd)


@router.get("/users", response_model=list[AdminUserSummary])
def list_users(
    status: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
    _admin: User = Depends(require_superadmin),
    db: Session = Depends(get_db),
) -> list[AdminUserSummary]:
    query = db.query(User)
    if status is not None:
        query = query.filter(User.status == status)
    users = query.order_by(User.created_at.desc()).offset(offset).limit(limit).all()
    if not users:
        return []

    user_ids = [user.id for user in users]
    count_rows = (
        db.query(WorkspaceMember.user_id, func.count(WorkspaceMember.id))
        .join(Workspace, Workspace.id == WorkspaceMember.workspace_id)
        .filter(WorkspaceMember.user_id.in_(user_ids), Workspace.is_deleted.is_(False))
        .group_by(WorkspaceMember.user_id)
        .all()
    )
    counts = {uid: int(cnt) for uid, cnt in count_rows}
    return [_to_user_summary(user, counts.get(user.id, 0)) for user in users]


@router.post("/users/{user_id}/suspend", response_model=AdminUserSummary)
def suspend_user(
    user_id: uuid.UUID,
    payload: SuspendUserRequest,
    request: Request,
    admin_user: User = Depends(require_superadmin),
    db: Session = Depends(get_db),
) -> AdminUserSummary:
    if user_id == admin_user.id:
        raise ValidationFailedError("Cannot suspend your own superadmin account.")
    user = db.get(User, user_id)
    if user is None:
        raise ResourceNotFoundError("User not found.")

    user.status = "SUSPENDED"
    user.token_version += 1
    db.query(APIKey).filter(
        APIKey.created_by_user_id == user.id,
        APIKey.is_active.is_(True),
    ).update({"is_active": False})

    record_audit_log(
        db,
        workspace_id=SYSTEM_WORKSPACE_ID,
        actor_user_id=admin_user.id,
        action="ADMIN_USER_SUSPENDED",
        target_entity=f"user:{user.id}",
        ip_address=get_client_ip(request),
        details={"email": user.email, "reason": payload.reason},
    )
    db.commit()
    db.refresh(user)
    return _to_user_summary(user, _user_workspace_count(db, user.id))


@router.post("/users/{user_id}/activate", response_model=AdminUserSummary)
def activate_user(
    user_id: uuid.UUID,
    request: Request,
    admin_user: User = Depends(require_superadmin),
    db: Session = Depends(get_db),
) -> AdminUserSummary:
    user = db.get(User, user_id)
    if user is None:
        raise ResourceNotFoundError("User not found.")

    user.status = "ACTIVE"
    record_audit_log(
        db,
        workspace_id=SYSTEM_WORKSPACE_ID,
        actor_user_id=admin_user.id,
        action="ADMIN_USER_ACTIVATED",
        target_entity=f"user:{user.id}",
        ip_address=get_client_ip(request),
        details={"email": user.email},
    )
    db.commit()
    db.refresh(user)
    return _to_user_summary(user, _user_workspace_count(db, user.id))


@router.get("/audit-logs", response_model=PaginatedAuditLogResponse)
def list_system_audit_logs(
    workspace_id: Annotated[uuid.UUID | None, Query()] = None,
    action: Annotated[str | None, Query()] = None,
    actor_user_id: Annotated[uuid.UUID | None, Query()] = None,
    date_from: Annotated[datetime | None, Query()] = None,
    date_to: Annotated[datetime | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    _admin: User = Depends(require_superadmin),
    db: Session = Depends(get_db),
) -> PaginatedAuditLogResponse:
    query = db.query(AuditLog)
    if workspace_id is not None:
        query = query.filter(AuditLog.workspace_id == workspace_id)
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


def _normalize_utc(dt: datetime) -> datetime:
    return dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt


def _workspace_sub_summary(
    workspace: Workspace, sub: Subscription, manager_emails: list[str]
) -> AdminWorkspaceSubscriptionSummary:
    return AdminWorkspaceSubscriptionSummary(
        workspace_id=str(workspace.id),
        workspace_name=workspace.name,
        tier=sub.tier,
        status=sub.status,
        monthly_report_quota=sub.monthly_report_quota,
        is_unlimited=sub.monthly_report_quota < 0,
        reports_used_this_month=sub.reports_used_this_month,
        custom_batch_limit=sub.custom_batch_limit,
        quota_reset_date=_normalize_utc(sub.quota_reset_date),
        payment_status=sub.payment_status,
        manager_emails=manager_emails,
        created_at=_normalize_utc(workspace.created_at),
    )


@router.get("/workspaces", response_model=list[AdminWorkspaceSubscriptionSummary])
def list_workspaces_for_admin(
    tier: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
    _admin: User = Depends(require_superadmin),
    db: Session = Depends(get_db),
) -> list[AdminWorkspaceSubscriptionSummary]:
    query = (
        db.query(Workspace, Subscription)
        .join(Subscription, Subscription.workspace_id == Workspace.id)
        .filter(Workspace.is_deleted.is_(False))
    )
    if tier:
        query = query.filter(Subscription.tier == tier.upper())
    rows = query.order_by(Workspace.created_at.desc()).offset(offset).limit(limit).all()
    if not rows:
        return []

    ws_ids = [ws.id for ws, _sub in rows]
    mgr_rows = (
        db.query(WorkspaceMember.workspace_id, User.email)
        .join(User, User.id == WorkspaceMember.user_id)
        .filter(
            WorkspaceMember.workspace_id.in_(ws_ids),
            WorkspaceMember.role == "MANAGER",
        )
        .all()
    )
    managers_by_ws: dict[uuid.UUID, list[str]] = {}
    for ws_id, email in mgr_rows:
        managers_by_ws.setdefault(ws_id, []).append(email)

    return [_workspace_sub_summary(ws, sub, managers_by_ws.get(ws.id, [])) for ws, sub in rows]


@router.patch(
    "/workspaces/{workspace_id}/subscription",
    response_model=AdminWorkspaceSubscriptionSummary,
)
def override_workspace_subscription(
    workspace_id: uuid.UUID,
    payload: AdminSubscriptionOverrideRequest,
    request: Request,
    admin_user: User = Depends(require_superadmin),
    db: Session = Depends(get_db),
) -> AdminWorkspaceSubscriptionSummary:
    workspace = db.get(Workspace, workspace_id)
    if workspace is None or workspace.is_deleted:
        raise ResourceNotFoundError("Workspace not found.")

    subscription = db.query(Subscription).filter_by(workspace_id=workspace_id).one_or_none()
    if subscription is None:
        raise ResourceNotFoundError("Subscription not found for this workspace.")

    prev_tier = subscription.tier
    prev_quota = subscription.monthly_report_quota
    subscription.tier = payload.tier
    subscription.monthly_report_quota = payload.monthly_report_quota
    subscription.custom_batch_limit = payload.custom_batch_limit
    subscription.status = "ACTIVE"
    if payload.tier in {"PRO", "ENTERPRISE"}:
        subscription.payment_status = "SETTLEMENT"

    record_audit_log(
        db,
        workspace_id=workspace.id,
        actor_user_id=admin_user.id,
        action="ADMIN_SUBSCRIPTION_OVERRIDDEN",
        target_entity=f"subscription:{subscription.id}",
        ip_address=get_client_ip(request),
        details={
            "previous_tier": prev_tier,
            "new_tier": payload.tier,
            "previous_quota": prev_quota,
            "new_quota": payload.monthly_report_quota,
            "custom_batch_limit": payload.custom_batch_limit,
            "reason": payload.reason,
        },
    )
    db.commit()
    db.refresh(subscription)

    mgr_emails = [
        row[0]
        for row in db.query(User.email)
        .join(WorkspaceMember, WorkspaceMember.user_id == User.id)
        .filter(WorkspaceMember.workspace_id == workspace.id, WorkspaceMember.role == "MANAGER")
        .all()
    ]
    return _workspace_sub_summary(workspace, subscription, mgr_emails)


def _inquiry_summary(inquiry: EnterpriseInquiry) -> EnterpriseInquiryResponse:
    return EnterpriseInquiryResponse(
        id=str(inquiry.id),
        workspace_id=str(inquiry.workspace_id) if inquiry.workspace_id else None,
        submitted_by_user_id=(
            str(inquiry.submitted_by_user_id) if inquiry.submitted_by_user_id else None
        ),
        company_name=inquiry.company_name,
        contact_name=inquiry.contact_name,
        contact_email=inquiry.contact_email,
        team_size=inquiry.team_size,
        estimated_monthly_reports=inquiry.estimated_monthly_reports,
        requirements=inquiry.requirements,
        status=cast(EnterpriseInquiryStatus, inquiry.status),
        admin_notes=inquiry.admin_notes,
        created_at=_normalize_utc(inquiry.created_at),
        updated_at=_normalize_utc(inquiry.updated_at),
    )


@router.get("/enterprise-inquiries", response_model=list[EnterpriseInquiryResponse])
def list_enterprise_inquiries(
    status: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    _admin: User = Depends(require_superadmin),
    db: Session = Depends(get_db),
) -> list[EnterpriseInquiryResponse]:
    query = db.query(EnterpriseInquiry)
    if status:
        query = query.filter(EnterpriseInquiry.status == status.upper())
    inquiries = (
        query.order_by(EnterpriseInquiry.created_at.desc()).offset(offset).limit(limit).all()
    )
    return [_inquiry_summary(item) for item in inquiries]


@router.patch("/enterprise-inquiries/{inquiry_id}", response_model=EnterpriseInquiryResponse)
def update_enterprise_inquiry(
    inquiry_id: uuid.UUID,
    payload: EnterpriseInquiryUpdateRequest,
    request: Request,
    admin_user: User = Depends(require_superadmin),
    db: Session = Depends(get_db),
) -> EnterpriseInquiryResponse:
    inquiry = db.get(EnterpriseInquiry, inquiry_id)
    if inquiry is None:
        raise ResourceNotFoundError("Enterprise inquiry not found.")

    inquiry.status = payload.status
    inquiry.admin_notes = payload.admin_notes
    record_audit_log(
        db,
        workspace_id=inquiry.workspace_id or SYSTEM_WORKSPACE_ID,
        actor_user_id=admin_user.id,
        action="ADMIN_ENTERPRISE_INQUIRY_UPDATED",
        target_entity=f"enterprise_inquiry:{inquiry.id}",
        ip_address=get_client_ip(request),
        details={"status": payload.status, "admin_notes": payload.admin_notes},
    )
    db.commit()
    db.refresh(inquiry)
    return _inquiry_summary(inquiry)
