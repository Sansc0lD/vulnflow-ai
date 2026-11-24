"""BillingRouter — PLAN.md FASE 4.8 (SDD §2.6.3, UC-16; EC-18 webhook idempotency)."""

import os
import secrets
import time
import uuid
from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from typing import Any, cast

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from redis.exceptions import RedisError
from sqlalchemy.orm import Session

from app.core.audit import get_client_ip, record_audit_log
from app.core.dependencies import get_db, require_workspace_role
from app.core.exceptions import (
    ConflictError,
    ResourceNotFoundError,
    ValidationFailedError,
)
from app.core.midtrans_signature import verify_midtrans_signature
from app.core.redis_client import get_optional_redis_client
from app.models.enterprise_inquiry import EnterpriseInquiry
from app.models.subscription import Subscription
from app.models.workspace_member import WorkspaceMember
from app.services.captcha_service import issue_inquiry_challenge, verify_inquiry_captcha
from app.services.email_service import (
    EmailSender,
    get_email_sender,
    send_enterprise_inquiry_notification,
)
from app.services.midtrans_adapter import MidtransAdapter, MidtransCheckoutError
from vulnflow_contracts import (
    EnterpriseInquiryChallengeResponse,
    EnterpriseInquiryCreateRequest,
    EnterpriseInquiryResponse,
    EnterpriseInquiryStatus,
    MidtransCheckoutRequest,
    MidtransCheckoutResponse,
    MidtransTransactionStatus,
    MidtransWebhookPayload,
    SubscriptionStatusResponse,
)

router = APIRouter(prefix="/api/v1/workspaces/{workspace_id}/billing", tags=["billing"])
webhook_router = APIRouter(prefix="/api/v1/billing", tags=["billing"])
public_enterprise_router = APIRouter(prefix="/api/v1/public", tags=["public"])

_PUBLIC_INQUIRY_RATE_LIMIT_PER_HOUR = 5

_require_manager = require_workspace_role({"MANAGER"})
_require_any_member = require_workspace_role({"MANAGER", "PENTESTER", "VIEWER"})

# ENTERPRISE isn't self-service priced anywhere in SDD §2.6.3 — only PRO has
# a published price ("$49 / Rp 750.000"); enterprise checkout is sales-led.
_TIER_PRICES_IDR = {"PRO": 750000}
_SETTLED_TRANSACTION_STATUSES = {
    MidtransTransactionStatus.SETTLEMENT,
    MidtransTransactionStatus.CAPTURE,
}
PRO_TIER_MONTHLY_REPORT_QUOTA = 30
FREE_TIER_MONTHLY_REPORT_QUOTA = 3


def get_midtrans_adapter() -> Generator[MidtransAdapter, None, None]:
    with httpx.Client(timeout=30.0) as client:
        yield MidtransAdapter(
            server_key=os.environ.get("MIDTRANS_SERVER_KEY", ""),
            client=client,
            is_production=os.environ.get("MIDTRANS_IS_PRODUCTION", "false").lower() == "true",
        )


def _normalize_utc(dt: datetime) -> datetime:
    return dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt


def _subscription_to_status(db: Session, subscription: Subscription) -> SubscriptionStatusResponse:
    now = datetime.now(UTC)
    reset_date = _normalize_utc(subscription.quota_reset_date)
    if now >= reset_date:
        subscription.reports_used_this_month = 0
        subscription.quota_reset_date = now + timedelta(days=30)
        db.commit()
        db.refresh(subscription)
        reset_date = _normalize_utc(subscription.quota_reset_date)

    is_unlimited = subscription.monthly_report_quota < 0
    remaining = (
        0
        if is_unlimited
        else max(0, subscription.monthly_report_quota - subscription.reports_used_this_month)
    )
    return SubscriptionStatusResponse(
        workspace_id=str(subscription.workspace_id),
        tier=subscription.tier,
        status=subscription.status,
        monthly_report_quota=subscription.monthly_report_quota,
        is_unlimited=is_unlimited,
        custom_batch_limit=subscription.custom_batch_limit,
        reports_used_this_month=subscription.reports_used_this_month,
        remaining_reports=remaining,
        quota_reset_date=reset_date,
        payment_status=subscription.payment_status,
        payment_type=subscription.payment_type,
        midtrans_order_id=subscription.midtrans_order_id,
    )


def _inquiry_to_response(inquiry: EnterpriseInquiry) -> EnterpriseInquiryResponse:
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
        created_at=inquiry.created_at,
        updated_at=inquiry.updated_at,
    )


@router.get("/subscription", response_model=SubscriptionStatusResponse)
def get_subscription_status(
    workspace_id: uuid.UUID,
    db: Session = Depends(get_db),
    _member: WorkspaceMember = Depends(_require_any_member),
) -> SubscriptionStatusResponse:
    subscription = db.query(Subscription).filter_by(workspace_id=workspace_id).one_or_none()
    if subscription is None:
        raise ResourceNotFoundError("No subscription found for this workspace.")
    return _subscription_to_status(db, subscription)


@router.post("/sync", response_model=SubscriptionStatusResponse)
def sync_subscription_status(
    workspace_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    adapter: MidtransAdapter = Depends(get_midtrans_adapter),
    current_member: WorkspaceMember = Depends(_require_manager),
) -> SubscriptionStatusResponse:
    subscription = db.query(Subscription).filter_by(workspace_id=workspace_id).one_or_none()
    if subscription is None:
        raise ResourceNotFoundError("No subscription found for this workspace.")
    if not subscription.midtrans_order_id:
        return _subscription_to_status(db, subscription)

    server_key = os.environ.get("MIDTRANS_SERVER_KEY", "")
    if not server_key or not server_key.strip():
        raise ValidationFailedError("Midtrans server key is not configured.")

    try:
        status_data = adapter.get_transaction_status(order_id=subscription.midtrans_order_id)
    except MidtransCheckoutError as exc:
        raise ValidationFailedError(f"Midtrans status sync failed: {exc}") from exc

    tx_status = str(status_data.get("transaction_status", "")).lower()
    fraud_status = str(status_data.get("fraud_status", "")).lower()
    payment_type = str(status_data.get("payment_type") or subscription.payment_type or "") or None
    ip_address = get_client_ip(request)

    if tx_status == "settlement" or (tx_status == "capture" and fraud_status in {"", "accept"}):
        if subscription.payment_status != "SETTLEMENT":
            subscription.tier = "PRO"
            subscription.monthly_report_quota = PRO_TIER_MONTHLY_REPORT_QUOTA
            subscription.payment_status = "SETTLEMENT"
            subscription.payment_type = payment_type
            record_audit_log(
                db,
                workspace_id=workspace_id,
                actor_user_id=current_member.user_id,
                action="SUBSCRIPTION_SYNCED_PRO",
                target_entity=f"subscription:{subscription.id}",
                ip_address=ip_address,
                details={
                    "order_id": subscription.midtrans_order_id,
                    "transaction_status": tx_status,
                },
            )
            db.commit()
    elif subscription.tier == "ENTERPRISE":
        return _subscription_to_status(db, subscription)
    elif tx_status in {"cancel", "deny"} or (tx_status == "capture" and fraud_status == "deny"):
        subscription.tier = "FREE"
        subscription.monthly_report_quota = FREE_TIER_MONTHLY_REPORT_QUOTA
        subscription.payment_status = "DENY" if fraud_status == "deny" else tx_status.upper()
        subscription.payment_type = payment_type
        record_audit_log(
            db,
            workspace_id=workspace_id,
            actor_user_id=current_member.user_id,
            action="SUBSCRIPTION_SYNCED_CANCELLED",
            target_entity=f"subscription:{subscription.id}",
            ip_address=ip_address,
            details={"order_id": subscription.midtrans_order_id, "transaction_status": tx_status},
        )
        db.commit()
    elif tx_status == "expire" and subscription.payment_status != "SETTLEMENT":
        subscription.tier = "FREE"
        subscription.monthly_report_quota = FREE_TIER_MONTHLY_REPORT_QUOTA
        subscription.payment_status = "EXPIRE"
        subscription.payment_type = payment_type
        record_audit_log(
            db,
            workspace_id=workspace_id,
            actor_user_id=current_member.user_id,
            action="SUBSCRIPTION_SYNCED_EXPIRED",
            target_entity=f"subscription:{subscription.id}",
            ip_address=ip_address,
            details={"order_id": subscription.midtrans_order_id},
        )
        db.commit()

    return _subscription_to_status(db, subscription)


@router.post("/checkout", response_model=MidtransCheckoutResponse)
def checkout(
    workspace_id: uuid.UUID,
    payload: MidtransCheckoutRequest,
    request: Request,
    db: Session = Depends(get_db),
    adapter: MidtransAdapter = Depends(get_midtrans_adapter),
    current_member: WorkspaceMember = Depends(_require_manager),
) -> MidtransCheckoutResponse:
    # F4-HIGH-01: Fail-closed if server key is not configured
    server_key = os.environ.get("MIDTRANS_SERVER_KEY", "")
    if not server_key or not server_key.strip():
        raise ValidationFailedError("Midtrans server key is not configured.")

    gross_amount = _TIER_PRICES_IDR.get(payload.tier.value)
    if gross_amount is None:
        raise ValidationFailedError(
            f"{payload.tier.value} is not available for self-service checkout."
        )

    subscription = db.query(Subscription).filter_by(workspace_id=workspace_id).one_or_none()
    if subscription is None:
        raise ResourceNotFoundError("No subscription found for this workspace.")
    if subscription.tier == "ENTERPRISE" or (
        subscription.tier == "PRO" and subscription.payment_status == "SETTLEMENT"
    ):
        raise ConflictError("Workspace already has an active paid subscription.")

    # Midtrans Snap enforces a 50-char max on order_id; prefix + timestamp + entropy is 45 chars.
    order_id = f"ORD-{workspace_id.hex[:24]}-{int(time.time())}-{secrets.token_hex(3)}"
    try:
        snap_token, redirect_url = adapter.create_transaction(
            order_id=order_id, gross_amount=gross_amount
        )
    except MidtransCheckoutError as exc:
        raise ValidationFailedError(f"Midtrans checkout failed: {exc}") from exc

    subscription.midtrans_order_id = order_id
    subscription.snap_token = snap_token
    subscription.payment_status = "PENDING"
    record_audit_log(
        db,
        workspace_id=workspace_id,
        actor_user_id=current_member.user_id,
        action="BILLING_CHECKOUT_CREATED",
        target_entity=f"subscription:{subscription.id}",
        ip_address=get_client_ip(request),
        details={"order_id": order_id, "tier": payload.tier.value, "gross_amount": gross_amount},
    )
    db.commit()

    return MidtransCheckoutResponse(
        order_id=order_id,
        gross_amount=gross_amount,
        snap_token=snap_token,
        redirect_url=redirect_url,
    )


@webhook_router.post("/webhook/midtrans")
def midtrans_webhook(
    payload: MidtransWebhookPayload,
    request: Request = None,  # type: ignore[assignment]
    db: Session = Depends(get_db),
) -> dict[str, str]:
    # F4-HIGH-01: Fail-closed if server key is empty/unset
    server_key = os.environ.get("MIDTRANS_SERVER_KEY", "")
    if not server_key or not server_key.strip():
        raise HTTPException(status_code=400, detail="Midtrans server key is not configured.")

    is_valid = verify_midtrans_signature(
        order_id=payload.order_id,
        status_code=payload.status_code,
        gross_amount=payload.gross_amount,
        signature_key=payload.signature_key,
        server_key=server_key,
    )
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid signature")

    subscription = (
        db.query(Subscription)
        .filter_by(midtrans_order_id=payload.order_id)
        .with_for_update()
        .one_or_none()
    )
    if subscription is None:
        return {"status": "OK"}  # unknown order_id — nothing to act on, but ack anyway

    ip_address = get_client_ip(request)
    fraud_status = (payload.fraud_status or "").lower()

    if (
        payload.transaction_status == MidtransTransactionStatus.CAPTURE
        and fraud_status == "challenge"
    ):
        subscription.payment_type = payload.payment_type
        db.commit()
        return {"status": "PENDING_REVIEW"}

    is_fraud_deny = (
        payload.transaction_status == MidtransTransactionStatus.CAPTURE and fraud_status == "deny"
    )

    if not is_fraud_deny and payload.transaction_status in _SETTLED_TRANSACTION_STATUSES:
        # F4-HIGH-02: validate gross_amount against expected tier price
        try:
            paid_amount = int(float(payload.gross_amount))
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="Invalid gross_amount format") from None

        if paid_amount < _TIER_PRICES_IDR["PRO"]:
            required = _TIER_PRICES_IDR["PRO"]
            raise HTTPException(
                status_code=400,
                detail=f"Paid amount {paid_amount} is less than required price {required}",
            )

        # F4-MED-15: Reject replay of settlement if the order is already in a terminal failed state
        if subscription.payment_status in {"EXPIRE", "CANCEL", "DENY"}:
            return {"status": "IGNORED_TERMINAL_ORDER"}

        subscription.payment_type = payload.payment_type
        # EC-18: a duplicate webhook for an already-settled order must not
        # re-apply the upgrade (idempotent no-op, not an error).
        if subscription.payment_status != "SETTLEMENT":
            subscription.tier = "PRO"
            subscription.monthly_report_quota = PRO_TIER_MONTHLY_REPORT_QUOTA
            subscription.payment_status = "SETTLEMENT"
            record_audit_log(
                db,
                workspace_id=subscription.workspace_id,
                actor_user_id=None,
                action="BILLING_WEBHOOK_SETTLED",
                target_entity=f"subscription:{subscription.id}",
                ip_address=ip_address,
                details={
                    "order_id": payload.order_id,
                    "payment_type": payload.payment_type,
                    "gross_amount": payload.gross_amount,
                },
            )
        db.commit()
        return {"status": "OK"}

    if (
        payload.transaction_status == MidtransTransactionStatus.EXPIRE
        and subscription.payment_status == "SETTLEMENT"
    ):
        return {"status": "IGNORED_ALREADY_SETTLED"}

    if subscription.tier == "ENTERPRISE":
        return {"status": "IGNORED_ENTERPRISE_PLAN"}

    # F4-MED-14: Downgrade tier to FREE on EXPIRE, CANCEL, DENY (or capture fraud_status=deny)
    if is_fraud_deny or payload.transaction_status in {
        MidtransTransactionStatus.EXPIRE,
        MidtransTransactionStatus.CANCEL,
        MidtransTransactionStatus.DENY,
    }:
        subscription.tier = "FREE"
        subscription.monthly_report_quota = FREE_TIER_MONTHLY_REPORT_QUOTA
        subscription.payment_type = payload.payment_type
        subscription.payment_status = (
            "DENY" if is_fraud_deny else payload.transaction_status.value.upper()
        )
        record_audit_log(
            db,
            workspace_id=subscription.workspace_id,
            actor_user_id=None,
            action="BILLING_WEBHOOK_CANCELLED",
            target_entity=f"subscription:{subscription.id}",
            ip_address=ip_address,
            details={
                "order_id": payload.order_id,
                "transaction_status": payload.transaction_status.value,
                "fraud_status": payload.fraud_status,
            },
        )
        db.commit()
        return {"status": "CANCELLED"}

    return {"status": "OK"}


@router.post("/enterprise-inquiry", response_model=EnterpriseInquiryResponse, status_code=201)
def create_workspace_enterprise_inquiry(
    workspace_id: uuid.UUID,
    payload: EnterpriseInquiryCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    email_sender: EmailSender = Depends(get_email_sender),
    redis_client: Any | None = Depends(get_optional_redis_client),
    current_member: WorkspaceMember = Depends(_require_manager),
) -> EnterpriseInquiryResponse:
    _enforce_inquiry_rate_limit(redis_client, f"workspace:{workspace_id}")
    inquiry = EnterpriseInquiry(
        workspace_id=workspace_id,
        submitted_by_user_id=current_member.user_id,
        company_name=payload.company_name,
        contact_name=payload.contact_name,
        contact_email=payload.contact_email,
        team_size=payload.team_size,
        estimated_monthly_reports=payload.estimated_monthly_reports,
        requirements=payload.requirements,
        status="NEW",
    )
    db.add(inquiry)
    db.flush()
    record_audit_log(
        db,
        workspace_id=workspace_id,
        actor_user_id=current_member.user_id,
        action="ENTERPRISE_INQUIRY_SUBMITTED",
        target_entity=f"enterprise_inquiry:{inquiry.id}",
        ip_address=get_client_ip(request),
        details={
            "company_name": payload.company_name,
            "contact_email": payload.contact_email,
            "team_size": payload.team_size,
        },
    )
    db.commit()
    db.refresh(inquiry)
    send_enterprise_inquiry_notification(
        email_sender,
        inquiry_id=str(inquiry.id),
        company_name=inquiry.company_name,
        contact_name=inquiry.contact_name,
        contact_email=inquiry.contact_email,
        team_size=inquiry.team_size,
        estimated_monthly_reports=inquiry.estimated_monthly_reports,
        requirements=inquiry.requirements,
        workspace_id=str(workspace_id),
    )
    return _inquiry_to_response(inquiry)


def _enforce_inquiry_rate_limit(redis_client: Any | None, scope_key: str) -> None:
    if redis_client is None:
        return
    key = f"ratelimit:enterprise_inquiry:{scope_key}"
    try:
        current = redis_client.incr(key)
        if int(current) == 1:
            redis_client.expire(key, 3600)
        if int(current) > _PUBLIC_INQUIRY_RATE_LIMIT_PER_HOUR:
            raise HTTPException(
                status_code=429,
                detail=(
                    "Too many Enterprise inquiries submitted recently. Please wait before retrying."
                ),
                headers={"Retry-After": "3600"},
            )
    except (RedisError, OSError, AttributeError):
        return


@public_enterprise_router.get(
    "/enterprise-inquiries/challenge",
    response_model=EnterpriseInquiryChallengeResponse,
)
def get_public_enterprise_inquiry_challenge() -> EnterpriseInquiryChallengeResponse:
    return issue_inquiry_challenge()


@public_enterprise_router.post(
    "/enterprise-inquiries", response_model=EnterpriseInquiryResponse, status_code=201
)
def submit_public_enterprise_inquiry(
    payload: EnterpriseInquiryCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    email_sender: EmailSender = Depends(get_email_sender),
    redis_client: Any | None = Depends(get_optional_redis_client),
) -> EnterpriseInquiryResponse:
    client_ip = get_client_ip(request)
    _enforce_inquiry_rate_limit(redis_client, f"ip:{client_ip}")
    verify_inquiry_captcha(
        captcha_token=payload.captcha_token,
        captcha_answer=payload.captcha_answer,
        remote_ip=client_ip,
        redis_client=redis_client,
    )
    inquiry = EnterpriseInquiry(
        workspace_id=None,
        submitted_by_user_id=None,
        company_name=payload.company_name,
        contact_name=payload.contact_name,
        contact_email=payload.contact_email,
        team_size=payload.team_size,
        estimated_monthly_reports=payload.estimated_monthly_reports,
        requirements=payload.requirements,
        status="NEW",
    )
    db.add(inquiry)
    db.commit()
    db.refresh(inquiry)
    send_enterprise_inquiry_notification(
        email_sender,
        inquiry_id=str(inquiry.id),
        company_name=inquiry.company_name,
        contact_name=inquiry.contact_name,
        contact_email=inquiry.contact_email,
        team_size=inquiry.team_size,
        estimated_monthly_reports=inquiry.estimated_monthly_reports,
        requirements=inquiry.requirements,
        workspace_id=None,
    )
    return _inquiry_to_response(inquiry)
