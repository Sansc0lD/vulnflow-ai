"""Tabel `audit_logs` — SDD §2.4.2 #11. Partisi bulanan: §2.4.4.

PostgreSQL declarative RANGE partitioning requires the partition key
(`created_at`) to be part of the primary key, hence the composite PK below
instead of a plain single-column `id` PK.
"""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, JSONVariant


def _utc_now() -> datetime:
    return datetime.now(UTC)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = ({"postgresql_partition_by": "RANGE (created_at)"},)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    # Client-side default (not server_default): this column is part of the
    # composite PK, and a server-generated value isn't known until after
    # INSERT, which breaks SQLAlchemy's post-commit identity-based refresh.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), primary_key=True, default=_utc_now
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), index=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    target_entity: Mapped[str] = mapped_column(String(50), nullable=False)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSONVariant, nullable=False)
