"""report_verification_and_project_tech_stack

Adds tamper-proof provenance columns (`sha256_hash`, `verification_code`,
`is_rasterized`, `is_signed`) to `reports`, and optional allowlisted
`tech_stack` JSON column to `projects` for stack-aware remediation guidance.

Revision ID: b2c3d4e5f602
Revises: a1b2c3d4e501
Create Date: 2026-11-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "b2c3d4e5f602"
down_revision: str | Sequence[str] | None = "a1b2c3d4e501"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("reports", sa.Column("sha256_hash", sa.String(length=64), nullable=True))
    op.add_column("reports", sa.Column("verification_code", sa.String(length=32), nullable=True))
    op.create_index(
        op.f("ix_reports_verification_code"),
        "reports",
        ["verification_code"],
        unique=True,
    )
    op.add_column(
        "reports",
        sa.Column(
            "is_rasterized",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.alter_column("reports", "is_rasterized", server_default=None)
    op.add_column(
        "reports",
        sa.Column(
            "is_signed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.alter_column("reports", "is_signed", server_default=None)

    op.add_column(
        "projects",
        sa.Column(
            "tech_stack",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("projects", "tech_stack")
    op.drop_column("reports", "is_signed")
    op.drop_column("reports", "is_rasterized")
    op.drop_index(op.f("ix_reports_verification_code"), table_name="reports")
    op.drop_column("reports", "verification_code")
    op.drop_column("reports", "sha256_hash")
