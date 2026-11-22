"""Tabel `enterprise_inquiries` for sales-led Enterprise onboarding (Issue #5)."""

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class EnterpriseInquiry(Base):
    __tablename__ = "enterprise_inquiries"
    __table_args__ = (
        CheckConstraint(
            "status IN ('NEW', 'CONTACTED', 'PROVISIONED', 'DECLINED')",
            name="ck_enterprise_inquiry_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("workspaces.id", ondelete="SET NULL"), nullable=True, index=True
    )
    submitted_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    company_name: Mapped[str] = mapped_column(String(150), nullable=False)
    contact_name: Mapped[str] = mapped_column(String(150), nullable=False)
    contact_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    team_size: Mapped[str] = mapped_column(String(50), default="5-20", nullable=False)
    estimated_monthly_reports: Mapped[int | None] = mapped_column(Integer, nullable=True)
    requirements: Mapped[str] = mapped_column(Text, default="", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="NEW", nullable=False)
    admin_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
