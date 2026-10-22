"""Tabel `ai_narratives` — SDD §2.4.2 #9."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, JSONVariant


class AINarrative(Base):
    __tablename__ = "ai_narratives"
    __table_args__ = (
        CheckConstraint(
            "approval_status IN ('DRAFT', 'APPROVED')", name="ck_ai_narrative_approval_status"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    executive_summary: Mapped[str] = mapped_column(Text, nullable=False)
    business_impact: Mapped[str] = mapped_column(Text, nullable=False)
    remediation_priorities: Mapped[list[Any]] = mapped_column(JSONVariant, nullable=False)
    tokens_consumed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_fallback: Mapped[bool] = mapped_column(default=False, nullable=False)  # EC-14
    approval_status: Mapped[str] = mapped_column(String(20), default="DRAFT", nullable=False)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
