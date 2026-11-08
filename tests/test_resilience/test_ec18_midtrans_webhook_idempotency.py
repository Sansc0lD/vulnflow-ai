"""PLAN.md FASE 7.2 — EC-18: Midtrans Webhook Idempotency.

EDGE_CASES_AND_RESILIENCE.md §5.3 & §6 item 18:
Midtrans may re-transmit webhook notifications multiple times due to network retries.
The `/billing/webhook/midtrans` handler must be strictly idempotent:
receiving duplicate settlement callbacks for the same order must update status once,
upgrade the quota to 30 once, and not double-increment quotas or fail.
"""

import hashlib
import uuid
from collections.abc import Generator
from datetime import UTC, datetime, timedelta

import pytest
from app.models.base import Base
from app.models.subscription import Subscription
from app.models.workspace import Workspace
from app.routers.billing import midtrans_webhook
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from vulnflow_contracts.billing_schemas import MidtransTransactionStatus, MidtransWebhookPayload


@pytest.fixture
def session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s
    engine.dispose()


def _sign(order_id: str, status_code: str, gross_amount: str, server_key: str) -> str:
    raw = f"{order_id}{status_code}{gross_amount}{server_key}"
    return hashlib.sha512(raw.encode()).hexdigest()


def test_ec18_duplicate_settlement_webhooks_processed_idempotently(
    session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Three identical settlement webhook calls for the same order upgrade quota only once."""
    workspace = Workspace(name="Billing Agency")
    session.add(workspace)
    session.commit()

    order_id = f"ORDER-{uuid.uuid4()}"
    server_key = "test-midtrans-secret-server-key"
    monkeypatch.setenv("MIDTRANS_SERVER_KEY", server_key)
    gross_amount = "750000.00"

    sub = Subscription(
        workspace_id=workspace.id,
        tier="FREE",
        monthly_report_quota=3,
        reports_used_this_month=0,
        payment_status="PENDING",
        midtrans_order_id=order_id,
        quota_reset_date=datetime.now(UTC) + timedelta(days=30),
    )
    session.add(sub)
    session.commit()

    sig = _sign(order_id, "200", gross_amount, server_key)
    payload = MidtransWebhookPayload(
        order_id=order_id,
        status_code="200",
        gross_amount=gross_amount,
        signature_key=sig,
        transaction_status=MidtransTransactionStatus.SETTLEMENT,
        payment_type="qris",
        transaction_time="2026-11-08 20:00:00",
    )

    # First webhook callback -> Upgrades to PRO (quota: 30)
    resp1 = midtrans_webhook(payload=payload, db=session)
    assert resp1 == {"status": "OK"}

    refreshed_1 = session.get(Subscription, sub.id)
    assert refreshed_1 is not None
    assert refreshed_1.tier == "PRO"
    assert refreshed_1.monthly_report_quota == 30
    assert refreshed_1.payment_status == "SETTLEMENT"

    # Second webhook callback (duplicate transmission) -> Idempotent no-op
    resp2 = midtrans_webhook(payload=payload, db=session)
    assert resp2 == {"status": "OK"}

    # Third webhook callback (another duplicate transmission) -> Idempotent no-op
    resp3 = midtrans_webhook(payload=payload, db=session)
    assert resp3 == {"status": "OK"}

    refreshed_final = session.get(Subscription, sub.id)
    assert refreshed_final is not None
    # Quota is still 30 (not 60 or 90)
    assert refreshed_final.tier == "PRO"
    assert refreshed_final.monthly_report_quota == 30
    assert refreshed_final.payment_status == "SETTLEMENT"
