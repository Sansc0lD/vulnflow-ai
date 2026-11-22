"""enterprise_inquiries_ai_tokens_and_batch_limit

Adds `enterprise_inquiries` table for sales-led Enterprise onboarding (#5),
`subscriptions.custom_batch_limit` for Enterprise batch sizing, and
`ai_narratives` token breakdown (`prompt_tokens`, `candidates_tokens`, `model_used`).

Revision ID: a1b2c3d4e501
Revises: f6c9a3b15d02
Create Date: 2026-11-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e501"
down_revision: str | Sequence[str] | None = "f6c9a3b15d02"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "enterprise_inquiries",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=True),
        sa.Column("submitted_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("company_name", sa.String(length=150), nullable=False),
        sa.Column("contact_name", sa.String(length=150), nullable=False),
        sa.Column("contact_email", sa.String(length=255), nullable=False),
        sa.Column("team_size", sa.String(length=50), nullable=False),
        sa.Column("estimated_monthly_reports", sa.Integer(), nullable=True),
        sa.Column("requirements", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("admin_notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('NEW', 'CONTACTED', 'PROVISIONED', 'DECLINED')",
            name="ck_enterprise_inquiry_status",
        ),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["submitted_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_enterprise_inquiries_workspace_id"),
        "enterprise_inquiries",
        ["workspace_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_enterprise_inquiries_submitted_by_user_id"),
        "enterprise_inquiries",
        ["submitted_by_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_enterprise_inquiries_contact_email"),
        "enterprise_inquiries",
        ["contact_email"],
        unique=False,
    )

    op.add_column(
        "subscriptions",
        sa.Column("custom_batch_limit", sa.Integer(), nullable=True),
    )

    op.add_column(
        "ai_narratives",
        sa.Column(
            "prompt_tokens",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.alter_column("ai_narratives", "prompt_tokens", server_default=None)
    op.add_column(
        "ai_narratives",
        sa.Column(
            "candidates_tokens",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.alter_column("ai_narratives", "candidates_tokens", server_default=None)
    op.add_column(
        "ai_narratives",
        sa.Column("model_used", sa.String(length=80), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("ai_narratives", "model_used")
    op.drop_column("ai_narratives", "candidates_tokens")
    op.drop_column("ai_narratives", "prompt_tokens")
    op.drop_column("subscriptions", "custom_batch_limit")
    op.drop_index(op.f("ix_enterprise_inquiries_contact_email"), table_name="enterprise_inquiries")
    op.drop_index(
        op.f("ix_enterprise_inquiries_submitted_by_user_id"), table_name="enterprise_inquiries"
    )
    op.drop_index(op.f("ix_enterprise_inquiries_workspace_id"), table_name="enterprise_inquiries")
    op.drop_table("enterprise_inquiries")
