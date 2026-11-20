"""PLAN.md FASE 4.8 — BillingRouter (SDD §2.6.3; EC-18 webhook idempotency)."""

import hashlib
import os
import uuid

import pytest
from app.main import app
from app.models.subscription import Subscription
from app.routers.billing import get_midtrans_adapter
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

_REGISTRATION = {
    "email": "billing@example.com",
    "password": "Str0ng!Passw0rd",
    "full_name": "Billing Tester",
    "workspace_name": "Agensi Billing",
}


class _FakeMidtransAdapter:
    def create_transaction(self, *, order_id: str, gross_amount: int) -> tuple[str, str]:
        return "snap-token-xyz", "https://app.sandbox.midtrans.com/snap/v3/redirection/xyz"


@pytest.fixture
def ctx(db_session: Session, monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    os.environ.setdefault("ENCRYPTION_MASTER_KEY", "9EL3Yj4ANNfiuFYY7zBoYc6XLnoD3GZpcBc6lWGLL9U=")
    monkeypatch.setenv("MIDTRANS_SERVER_KEY", "test-server-key")
    app.dependency_overrides[get_midtrans_adapter] = lambda: _FakeMidtransAdapter()
    with TestClient(app) as client:
        register = client.post("/api/v1/auth/register", json=_REGISTRATION).json()
    yield {"workspace_id": register["workspace_id"], "token": register["access_token"]}
    app.dependency_overrides.pop(get_midtrans_adapter, None)


def _auth(ctx: dict[str, str]) -> dict[str, str]:
    return {"Authorization": f"Bearer {ctx['token']}"}


def _sign(order_id: str, status_code: str, gross_amount: str, server_key: str) -> str:
    raw = f"{order_id}{status_code}{gross_amount}{server_key}"
    return hashlib.sha512(raw.encode()).hexdigest()


def test_checkout_returns_snap_token_and_persists_order(
    db_session: Session, ctx: dict[str, str]
) -> None:
    with TestClient(app) as client:
        response = client.post(
            f"/api/v1/workspaces/{ctx['workspace_id']}/billing/checkout",
            json={"tier": "PRO"},
            headers=_auth(ctx),
        )

    assert response.status_code == 200
    body = response.json()
    assert body["snap_token"] == "snap-token-xyz"
    assert body["gross_amount"] == 750000

    subscription = (
        db_session.query(Subscription).filter_by(workspace_id=uuid.UUID(ctx["workspace_id"])).one()
    )
    assert subscription.midtrans_order_id == body["order_id"]
    assert subscription.snap_token == "snap-token-xyz"
    assert subscription.payment_status == "PENDING"


def test_checkout_rejects_non_manager(ctx: dict[str, str]) -> None:
    with TestClient(app) as client:
        invite = client.post(
            f"/api/v1/workspaces/{ctx['workspace_id']}/members",
            json={"email": "billing-viewer@example.com", "role": "VIEWER"},
            headers=_auth(ctx),
        ).json()["invitation_token"]
        viewer_token = client.post(
            "/api/v1/auth/register",
            json={
                "email": "billing-viewer@example.com",
                "password": "Str0ng!Passw0rd",
                "full_name": "Viewer",
                "workspace_name": "Unused",
                "invitation_token": invite,
            },
        ).json()["access_token"]

        response = client.post(
            f"/api/v1/workspaces/{ctx['workspace_id']}/billing/checkout",
            json={"tier": "PRO"},
            headers={"Authorization": f"Bearer {viewer_token}"},
        )

    assert response.status_code == 403


def test_webhook_upgrades_subscription_on_valid_settlement(
    db_session: Session, ctx: dict[str, str]
) -> None:
    with TestClient(app) as client:
        checkout = client.post(
            f"/api/v1/workspaces/{ctx['workspace_id']}/billing/checkout",
            json={"tier": "PRO"},
            headers=_auth(ctx),
        ).json()
        order_id = checkout["order_id"]
        signature = _sign(order_id, "200", "750000.00", "test-server-key")

        response = client.post(
            "/api/v1/billing/webhook/midtrans",
            json={
                "order_id": order_id,
                "status_code": "200",
                "gross_amount": "750000.00",
                "signature_key": signature,
                "transaction_status": "settlement",
                "payment_type": "qris",
                "transaction_time": "2026-10-24 10:00:00",
            },
        )

    assert response.status_code == 200
    subscription = (
        db_session.query(Subscription).filter_by(workspace_id=uuid.UUID(ctx["workspace_id"])).one()
    )
    assert subscription.tier == "PRO"
    assert subscription.monthly_report_quota == 30
    assert subscription.payment_status == "SETTLEMENT"


def test_webhook_rejects_invalid_signature(db_session: Session, ctx: dict[str, str]) -> None:
    with TestClient(app) as client:
        checkout = client.post(
            f"/api/v1/workspaces/{ctx['workspace_id']}/billing/checkout",
            json={"tier": "PRO"},
            headers=_auth(ctx),
        ).json()

        response = client.post(
            "/api/v1/billing/webhook/midtrans",
            json={
                "order_id": checkout["order_id"],
                "status_code": "200",
                "gross_amount": "750000.00",
                "signature_key": "0" * 128,
                "transaction_status": "settlement",
                "payment_type": "qris",
                "transaction_time": "2026-10-24 10:00:00",
            },
        )

    assert response.status_code == 400


def test_webhook_duplicate_settlement_does_not_double_process(
    db_session: Session, ctx: dict[str, str]
) -> None:
    # EC-18.
    with TestClient(app) as client:
        checkout = client.post(
            f"/api/v1/workspaces/{ctx['workspace_id']}/billing/checkout",
            json={"tier": "PRO"},
            headers=_auth(ctx),
        ).json()
        order_id = checkout["order_id"]
        signature = _sign(order_id, "200", "750000.00", "test-server-key")
        webhook_body = {
            "order_id": order_id,
            "status_code": "200",
            "gross_amount": "750000.00",
            "signature_key": signature,
            "transaction_status": "settlement",
            "payment_type": "qris",
            "transaction_time": "2026-10-24 10:00:00",
        }

        first = client.post("/api/v1/billing/webhook/midtrans", json=webhook_body)
        second = client.post("/api/v1/billing/webhook/midtrans", json=webhook_body)

    assert first.status_code == 200
    assert second.status_code == 200
    subscription = (
        db_session.query(Subscription).filter_by(workspace_id=uuid.UUID(ctx["workspace_id"])).one()
    )
    assert subscription.tier == "PRO"  # still correct, not corrupted by replay


def test_webhook_expire_sets_payment_status_without_upgrading(
    db_session: Session, ctx: dict[str, str]
) -> None:
    with TestClient(app) as client:
        checkout = client.post(
            f"/api/v1/workspaces/{ctx['workspace_id']}/billing/checkout",
            json={"tier": "PRO"},
            headers=_auth(ctx),
        ).json()
        order_id = checkout["order_id"]
        signature = _sign(order_id, "200", "750000.00", "test-server-key")

        response = client.post(
            "/api/v1/billing/webhook/midtrans",
            json={
                "order_id": order_id,
                "status_code": "200",
                "gross_amount": "750000.00",
                "signature_key": signature,
                "transaction_status": "expire",
                "payment_type": "qris",
                "transaction_time": "2026-10-24 10:00:00",
            },
        )

    assert response.status_code == 200
    subscription = (
        db_session.query(Subscription).filter_by(workspace_id=uuid.UUID(ctx["workspace_id"])).one()
    )
    assert subscription.tier == "FREE"  # unchanged
    assert subscription.payment_status == "EXPIRE"


def test_checkout_fails_closed_when_server_key_missing(
    ctx: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    # F4-HIGH-01
    monkeypatch.setenv("MIDTRANS_SERVER_KEY", "")
    with TestClient(app) as client:
        response = client.post(
            f"/api/v1/workspaces/{ctx['workspace_id']}/billing/checkout",
            json={"tier": "PRO"},
            headers=_auth(ctx),
        )
    assert response.status_code == 422


def test_webhook_fails_closed_when_server_key_missing(
    ctx: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    # F4-HIGH-01
    monkeypatch.setenv("MIDTRANS_SERVER_KEY", "")
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/billing/webhook/midtrans",
            json={
                "order_id": "ORD-123",
                "status_code": "200",
                "gross_amount": "750000.00",
                "signature_key": "0" * 128,
                "transaction_status": "settlement",
                "payment_type": "qris",
                "transaction_time": "2026-10-24 10:00:00",
            },
        )
    assert response.status_code == 400


def test_webhook_rejects_insufficient_gross_amount(
    db_session: Session, ctx: dict[str, str]
) -> None:
    # F4-HIGH-02: Tampered/insufficient gross amount is rejected with 400
    with TestClient(app) as client:
        checkout = client.post(
            f"/api/v1/workspaces/{ctx['workspace_id']}/billing/checkout",
            json={"tier": "PRO"},
            headers=_auth(ctx),
        ).json()
        order_id = checkout["order_id"]
        # Signature generated for tampered amount 50000.00
        signature = _sign(order_id, "200", "50000.00", "test-server-key")

        response = client.post(
            "/api/v1/billing/webhook/midtrans",
            json={
                "order_id": order_id,
                "status_code": "200",
                "gross_amount": "50000.00",
                "signature_key": signature,
                "transaction_status": "settlement",
                "payment_type": "qris",
                "transaction_time": "2026-10-24 10:00:00",
            },
        )
    assert response.status_code == 400
    assert "less than required price" in response.text


def test_webhook_downgrades_to_free_on_cancel_or_deny(
    db_session: Session, ctx: dict[str, str]
) -> None:
    # F4-MED-14
    with TestClient(app) as client:
        checkout = client.post(
            f"/api/v1/workspaces/{ctx['workspace_id']}/billing/checkout",
            json={"tier": "PRO"},
            headers=_auth(ctx),
        ).json()
        order_id = checkout["order_id"]

        # First settle it to PRO
        sig_settle = _sign(order_id, "200", "750000.00", "test-server-key")
        client.post(
            "/api/v1/billing/webhook/midtrans",
            json={
                "order_id": order_id,
                "status_code": "200",
                "gross_amount": "750000.00",
                "signature_key": sig_settle,
                "transaction_status": "settlement",
                "payment_type": "qris",
                "transaction_time": "2026-10-24 10:00:00",
            },
        )
        subscription = (
            db_session.query(Subscription)
            .filter_by(workspace_id=uuid.UUID(ctx["workspace_id"]))
            .one()
        )
        assert subscription.tier == "PRO"

        # Now send CANCEL webhook
        sig_cancel = _sign(order_id, "200", "750000.00", "test-server-key")
        resp = client.post(
            "/api/v1/billing/webhook/midtrans",
            json={
                "order_id": order_id,
                "status_code": "200",
                "gross_amount": "750000.00",
                "signature_key": sig_cancel,
                "transaction_status": "cancel",
                "payment_type": "qris",
                "transaction_time": "2026-10-24 10:05:00",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "CANCELLED"
        db_session.refresh(subscription)
        assert subscription.tier == "FREE"
        assert subscription.monthly_report_quota == 3
        assert subscription.payment_status == "CANCEL"

        # F4-NEW-01 regression: a real "deny" notification must not 500.
        # `payment_status` is set to the upper-cased transaction_status, and
        # 'DENY' was missing from `ck_subscription_payment_status`, so this
        # previously raised an uncaught IntegrityError on db.commit().
        sig_deny = _sign(order_id, "200", "750000.00", "test-server-key")
        resp_deny = client.post(
            "/api/v1/billing/webhook/midtrans",
            json={
                "order_id": order_id,
                "status_code": "200",
                "gross_amount": "750000.00",
                "signature_key": sig_deny,
                "transaction_status": "deny",
                "payment_type": "qris",
                "transaction_time": "2026-10-24 10:10:00",
            },
        )
        assert resp_deny.status_code == 200
        assert resp_deny.json()["status"] == "CANCELLED"
        db_session.refresh(subscription)
        assert subscription.payment_status == "DENY"


def test_webhook_ignores_settlement_on_terminal_order(
    db_session: Session, ctx: dict[str, str]
) -> None:
    # F4-MED-15: Reject settlement replay on terminal orders (EXPIRE/CANCEL/DENY)
    with TestClient(app) as client:
        checkout = client.post(
            f"/api/v1/workspaces/{ctx['workspace_id']}/billing/checkout",
            json={"tier": "PRO"},
            headers=_auth(ctx),
        ).json()
        order_id = checkout["order_id"]

        # Send EXPIRE first
        sig_expire = _sign(order_id, "200", "750000.00", "test-server-key")
        client.post(
            "/api/v1/billing/webhook/midtrans",
            json={
                "order_id": order_id,
                "status_code": "200",
                "gross_amount": "750000.00",
                "signature_key": sig_expire,
                "transaction_status": "expire",
                "payment_type": "qris",
                "transaction_time": "2026-10-24 10:00:00",
            },
        )
        subscription = (
            db_session.query(Subscription)
            .filter_by(workspace_id=uuid.UUID(ctx["workspace_id"]))
            .one()
        )
        assert subscription.payment_status == "EXPIRE"

        # Now attempt settlement replay on the expired order
        sig_settle = _sign(order_id, "200", "750000.00", "test-server-key")
        resp = client.post(
            "/api/v1/billing/webhook/midtrans",
            json={
                "order_id": order_id,
                "status_code": "200",
                "gross_amount": "750000.00",
                "signature_key": sig_settle,
                "transaction_status": "settlement",
                "payment_type": "qris",
                "transaction_time": "2026-10-24 10:10:00",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "IGNORED_TERMINAL_ORDER"
        db_session.refresh(subscription)
        assert subscription.payment_status == "EXPIRE"
        assert subscription.tier == "FREE"


def test_subscription_status_sync_fraud_challenge_and_delayed_expire(
    db_session: Session, ctx: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    from datetime import UTC, datetime, timedelta

    from app.routers.billing import get_midtrans_adapter

    monkeypatch.setenv("MIDTRANS_SERVER_KEY", "test-server-key")

    class _FakeSyncAdapter:
        def __init__(self, status_payload: dict[str, str]) -> None:
            self._status_payload = status_payload

        def create_transaction(self, *, order_id: str, gross_amount: int) -> tuple[str, str]:
            return "snap-tok", "https://snap.local/pay"

        def get_transaction_status(self, *, order_id: str) -> dict[str, str]:
            return self._status_payload

    billing_base = f"/api/v1/workspaces/{ctx['workspace_id']}/billing"
    app.dependency_overrides[get_midtrans_adapter] = lambda: _FakeSyncAdapter(
        {
            "order_id": "ignored",
            "transaction_status": "settlement",
            "payment_type": "qris",
        }
    )
    try:
        with TestClient(app) as client:
            sub = (
                db_session.query(Subscription)
                .filter_by(workspace_id=uuid.UUID(ctx["workspace_id"]))
                .one()
            )
            sub.reports_used_this_month = 2
            sub.quota_reset_date = datetime.now(UTC) - timedelta(days=1)
            db_session.commit()

            st = client.get(f"{billing_base}/subscription", headers=_auth(ctx))
            assert st.status_code == 200
            assert st.json()["reports_used_this_month"] == 0
            assert st.json()["remaining_reports"] == 3

            checkout = client.post(
                f"{billing_base}/checkout", json={"tier": "PRO"}, headers=_auth(ctx)
            ).json()
            order_id = checkout["order_id"]

            # CAPTURE with fraud_status=challenge stays PENDING_REVIEW
            sig = _sign(order_id, "200", "750000.00", "test-server-key")
            ch_resp = client.post(
                "/api/v1/billing/webhook/midtrans",
                json={
                    "order_id": order_id,
                    "status_code": "200",
                    "gross_amount": "750000.00",
                    "signature_key": sig,
                    "transaction_status": "capture",
                    "payment_type": "credit_card",
                    "transaction_time": "2026-10-24 10:00:00",
                    "fraud_status": "challenge",
                },
            )
            assert ch_resp.json()["status"] == "PENDING_REVIEW"

            # Sync upgrades to PRO via Midtrans status check
            synced = client.post(f"{billing_base}/sync", headers=_auth(ctx))
            assert synced.status_code == 200
            assert synced.json()["tier"] == "PRO"
            assert synced.json()["payment_status"] == "SETTLEMENT"

            # Delayed EXPIRE on already settled order is ignored without downgrading
            exp_resp = client.post(
                "/api/v1/billing/webhook/midtrans",
                json={
                    "order_id": order_id,
                    "status_code": "200",
                    "gross_amount": "750000.00",
                    "signature_key": sig,
                    "transaction_status": "expire",
                    "payment_type": "qris",
                    "transaction_time": "2026-10-24 10:15:00",
                },
            )
            assert exp_resp.json()["status"] == "IGNORED_ALREADY_SETTLED"
            db_session.refresh(sub)
            assert sub.tier == "PRO"
    finally:
        app.dependency_overrides.pop(get_midtrans_adapter, None)
