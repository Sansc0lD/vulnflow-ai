"""widen_audit_log_target_entity

Widen `audit_logs.target_entity` from VARCHAR(50) to VARCHAR(128) so entity
prefixes combined with 36-char UUIDs (such as `enterprise_inquiry:<uuid>`,
55 chars) or long invitation emails do not fail with PostgreSQL
StringDataRightTruncation.

Revision ID: c3d4e5f6a703
Revises: b2c3d4e5f602
Create Date: 2026-11-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c3d4e5f6a703"
down_revision: str | Sequence[str] | None = "b2c3d4e5f602"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Widen `audit_logs.target_entity` column to 128 chars."""
    op.alter_column(
        "audit_logs",
        "target_entity",
        existing_type=sa.String(length=50),
        type_=sa.String(length=128),
        existing_nullable=False,
    )


def downgrade() -> None:
    """Revert `audit_logs.target_entity` column width back to 50 chars."""
    op.alter_column(
        "audit_logs",
        "target_entity",
        existing_type=sa.String(length=128),
        type_=sa.String(length=50),
        existing_nullable=False,
    )
