"""PLAN.md FASE 2.3 — Tabel `subscriptions` (SDD §2.4.2 #4)."""

from datetime import UTC, datetime

import pytest
from app.models.subscription import Subscription
from app.models.workspace import Workspace
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


def test_create_subscription_applies_free_tier_defaults(session: Session) -> None:
    workspace = Workspace(name="Agensi")
    session.add(workspace)
    session.commit()

    subscription = Subscription(
        workspace_id=workspace.id, quota_reset_date=datetime(2026, 11, 1, tzinfo=UTC)
    )
    session.add(subscription)
    session.commit()

    assert subscription.tier == "FREE"
    assert subscription.monthly_report_quota == 3
    assert subscription.reports_used_this_month == 0
    assert subscription.payment_status == "PENDING"


def test_subscription_is_unique_per_workspace(session: Session) -> None:
    workspace = Workspace(name="Agensi")
    session.add(workspace)
    session.commit()
    reset_date = datetime(2026, 11, 1, tzinfo=UTC)

    session.add(Subscription(workspace_id=workspace.id, quota_reset_date=reset_date))
    session.commit()
    session.add(Subscription(workspace_id=workspace.id, quota_reset_date=reset_date))

    with pytest.raises(IntegrityError):
        session.commit()
