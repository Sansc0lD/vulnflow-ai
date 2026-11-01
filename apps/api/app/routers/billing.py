"""BillingRouter — PLAN.md FASE 4.8 (SDD §2.6.3, UC-16; EC-18 webhook idempotency)."""

import os
import time
import uuid

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_workspace_role
from app.core.exceptions import ResourceNotFoundError, ValidationFailedError
from app.core.midtrans_signature import verify_midtrans_signature
from app.models.subscription import Subscription
from app.models.workspace_member import WorkspaceMember
from app.services.midtrans_adapter import MidtransAdapter, MidtransCheckoutError
from vulnflow_contracts import (
    MidtransCheckoutRequest,
    MidtransCheckoutResponse,
    MidtransTransactionStatus,
    MidtransWebhookPayload,
)

router = APIRouter(prefix="/api/v1/workspaces/{workspace_id}/billing", tags=["billing"])
webhook_router = APIRouter(prefix="/api/v1/billing", tags=["billing"])

_require_manager = require_workspace_role({"MANAGER"})

# ENTERPRISE isn't self-service priced anywhere in SDD §2.6.3 — only PRO has
# a published price ("$49 / Rp 750.000"); enterprise checkout is sales-led.
_TIER_PRICES_IDR = {"PRO": 750000}
_SETTLED_TRANSACTION_STATUSES = {
    MidtransTransactionStatus.SETTLEMENT,
    MidtransTransactionStatus.CAPTURE,
}
PRO_TIER_MONTHLY_REPORT_QUOTA = 30


def get_midtrans_adapter() -> MidtransAdapter:
    return MidtransAdapter(
        server_key=os.environ.get("MIDTRANS_SERVER_KEY", ""),
        client=httpx.Client(timeout=30.0),
        is_production=os.environ.get("MIDTRANS_IS_PRODUCTION", "false").lower() == "true",
    )


@router.post("/checkout", response_model=MidtransCheckoutResponse)
def checkout(
    workspace_id: uuid.UUID,
    payload: MidtransCheckoutRequest,
    db: Session = Depends(get_db),
    adapter: MidtransAdapter = Depends(get_midtrans_adapter),
    _member: WorkspaceMember = Depends(_require_manager),
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

    order_id = f"ORD-{workspace_id}-{int(time.time())}"
    try:
        snap_token, redirect_url = adapter.create_transaction(
            order_id=order_id, gross_amount=gross_amount
        )
    except MidtransCheckoutError as exc:
        raise ValidationFailedError(f"Midtrans checkout failed: {exc}") from exc

    subscription.midtrans_order_id = order_id
    subscription.snap_token = snap_token
    subscription.payment_status = "PENDING"
    db.commit()

    return MidtransCheckoutResponse(
        order_id=order_id,
        gross_amount=gross_amount,
        snap_token=snap_token,
        redirect_url=redirect_url,
    )


@webhook_router.post("/webhook/midtrans")
def midtrans_webhook(
    payload: MidtransWebhookPayload, db: Session = Depends(get_db)
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
        db.query(Subscription).filter_by(midtrans_order_id=payload.order_id).one_or_none()
    )
    if subscription is None:
        return {"status": "OK"}  # unknown order_id — nothing to act on, but ack anyway

    if payload.transaction_status in _SETTLED_TRANSACTION_STATUSES:
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

        # EC-18: a duplicate webhook for an already-settled order must not
        # re-apply the upgrade (idempotent no-op, not an error).
        if subscription.payment_status != "SETTLEMENT":
            subscription.tier = "PRO"
            subscription.monthly_report_quota = PRO_TIER_MONTHLY_REPORT_QUOTA
            subscription.payment_status = "SETTLEMENT"
            db.commit()
        return {"status": "OK"}

    # F4-MED-14: Downgrade tier to FREE on EXPIRE, CANCEL, or DENY
    if payload.transaction_status in {
        MidtransTransactionStatus.EXPIRE,
        MidtransTransactionStatus.CANCEL,
        MidtransTransactionStatus.DENY,
    }:
        subscription.tier = "FREE"
        subscription.monthly_report_quota = 3
        subscription.payment_status = payload.transaction_status.value.upper()
        db.commit()
        return {"status": "CANCELLED"}

    return {"status": "OK"}
