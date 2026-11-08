"""allow_deny_payment_status

The Midtrans webhook handler (`routers/billing.py`) sets `payment_status` to
the upper-cased `transaction_status` for EXPIRE/CANCEL/DENY notifications,
but `ck_subscription_payment_status` only allowed PENDING/SETTLEMENT/EXPIRE/
CANCEL — a real `deny` notification from Midtrans (a card declined, say)
made the webhook's own `db.commit()` raise `IntegrityError`, which the
router never catches, producing an uncaught 500 on a public, unauthenticated
endpoint instead of the intended downgrade-to-FREE. Found because the
regression test named `..._cancel_or_deny` never actually sent a `deny`
payload.

A separate new revision rather than editing an already-applied one in
place: Alembic tracks revision IDs, not file content, so appending an ALTER
to a migration a database has already run (as a prior pass on this fix did,
to `d4a7f1c93b28`) is a no-op on that database forever — confirmed by
actually running `alembic upgrade head` against a real `docker compose`
Postgres already at `d4a7f1c93b28`: no error, no change, constraint still
missing `'DENY'`.

Revision ID: e5b8f2a04c91
Revises: d4a7f1c93b28
Create Date: 2026-11-01

"""

from collections.abc import Sequence

from alembic import op

revision: str = "e5b8f2a04c91"
down_revision: str | Sequence[str] | None = "d4a7f1c93b28"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint("ck_subscription_payment_status", "subscriptions", type_="check")
    op.create_check_constraint(
        "ck_subscription_payment_status",
        "subscriptions",
        "payment_status IN ('PENDING', 'SETTLEMENT', 'EXPIRE', 'CANCEL', 'DENY')",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("ck_subscription_payment_status", "subscriptions", type_="check")
    op.create_check_constraint(
        "ck_subscription_payment_status",
        "subscriptions",
        "payment_status IN ('PENDING', 'SETTLEMENT', 'EXPIRE', 'CANCEL')",
    )
