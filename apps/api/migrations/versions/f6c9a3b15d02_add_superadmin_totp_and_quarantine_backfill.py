"""add_superadmin_totp_and_quarantine_backfill

Adds `users.is_superadmin` and `users.totp_secret` for SaaS Superadmin
operations (UC-17..UC-19) with 6-digit TOTP MFA, and backfills
`is_curated_for_report = false` for any quarantined findings (BL-02).

Revision ID: f6c9a3b15d02
Revises: e5b8f2a04c91
Create Date: 2026-11-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f6c9a3b15d02"
down_revision: str | Sequence[str] | None = "e5b8f2a04c91"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "users",
        sa.Column(
            "is_superadmin",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.alter_column("users", "is_superadmin", server_default=None)
    op.add_column("users", sa.Column("totp_secret", sa.String(length=64), nullable=True))
    op.execute("UPDATE findings SET is_curated_for_report = false WHERE is_quarantined = true")


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "totp_secret")
    op.drop_column("users", "is_superadmin")
