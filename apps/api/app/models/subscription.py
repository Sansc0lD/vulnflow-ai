"""Tabel `subscriptions` — SDD §2.4.2 #4."""

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Subscription(Base):
    __tablename__ = "subscriptions"
    __table_args__ = (
        CheckConstraint("tier IN ('FREE', 'PRO', 'ENTERPRISE')", name="ck_subscription_tier"),
        CheckConstraint("status IN ('ACTIVE', 'INACTIVE')", name="ck_subscription_status"),
        CheckConstraint(
            "payment_status IN ('PENDING', 'SETTLEMENT', 'EXPIRE', 'CANCEL', 'DENY')",
            name="ck_subscription_payment_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    tier: Mapped[str] = mapped_column(String(20), default="FREE", nullable=False)
    monthly_report_quota: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    reports_used_this_month: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    quota_reset_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", nullable=False)
    # Unique (SDD §2.4.2 #4 "Kode referensi order unik Midtrans"): the webhook
    # resolves a subscription with `.one_or_none()` on this column, which would
    # raise MultipleResultsFound — an HTTP 500 on an unauthenticated endpoint —
    # if two rows ever shared an order id. NULLs are distinct in PostgreSQL, so
    # subscriptions that never checked out are unaffected.
    midtrans_order_id: Mapped[str | None] = mapped_column(String(100), unique=True, index=True)
    payment_type: Mapped[str | None] = mapped_column(String(50))
    snap_token: Mapped[str | None] = mapped_column(String(255))
    payment_status: Mapped[str] = mapped_column(String(30), default="PENDING", nullable=False)
