"""Tabel `projects` — SDD §2.4.2 #6."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, JSONVariant


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (
        CheckConstraint("status IN ('ACTIVE', 'ARCHIVED')", name="ck_project_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Nullable by design (a project may have no assigned PIC), so SET NULL is
    # the honest delete rule: losing the lead must not orphan or silently
    # delete the audit project. Left at the default NO ACTION it raised a raw
    # IntegrityError (HTTP 500) on any account deletion instead of the
    # `409 Conflict` EC-03 specifies — the 409 guard belongs on
    # `workspace_members.user_id`, which is where it now lives.
    lead_pentester_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    client_name: Mapped[str] = mapped_column(String(150), nullable=False)
    target_scope: Mapped[str] = mapped_column(Text, nullable=False)
    roe_start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    roe_end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", nullable=False)
    tech_stack: Mapped[dict[str, Any] | None] = mapped_column(JSONVariant, nullable=True)
