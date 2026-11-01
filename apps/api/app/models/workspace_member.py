"""Tabel `workspace_members` — SDD §2.4.2 #3."""

import uuid

from sqlalchemy import CheckConstraint, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class WorkspaceMember(Base):
    __tablename__ = "workspace_members"
    __table_args__ = (
        UniqueConstraint("workspace_id", "user_id", name="uq_workspace_member"),
        CheckConstraint(
            "role IN ('MANAGER', 'PENTESTER', 'VIEWER')", name="ck_workspace_member_role"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # No ondelete action (NO ACTION / RESTRICT), which is what makes EC-03
    # enforceable: SDD §2.7.1 states the database must *reject* deleting an
    # account before ownership is transferred. With ON DELETE CASCADE the
    # DELETE succeeded and silently took the membership row with it, leaving a
    # workspace with zero members — unreachable through `require_workspace_role`
    # yet still holding its projects, findings and encrypted PoCs: precisely
    # the orphaned workspace EC-03 exists to prevent. Deleting a workspace
    # still cascades to its members via `workspace_id` above.
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
