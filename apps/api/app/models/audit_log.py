"""Tabel `audit_logs` — SDD §2.4.2 #11. Partisi bulanan: §2.4.4.

PostgreSQL declarative RANGE partitioning requires the partition key
(`created_at`) to be part of the primary key, hence the composite PK below
instead of a plain single-column `id` PK.
"""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, Uuid
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
    # Deliberately NOT a foreign key. SRS UC-04 E2 step 2 and UC-19 E1 require
    # audit rows to outlive the permanent purge of their workspace ("tetap
    # tersimpan sebagai referensi historis ... tidak di-cascade-delete") as
    # platform compliance evidence. An FK cannot express that: ON DELETE
    # CASCADE destroys the very rows that must be kept — including the
    # WORKSPACE_PURGED entry written moments earlier — and it does so through
    # a referential-integrity trigger that runs with the table owner's rights,
    # so the "REVOKE DELETE ON audit_logs" control in SDD §2.4.4 does not stop
    # it. ON DELETE RESTRICT would instead make the purge impossible. The
    # column therefore keeps the workspace id as a dangling historical
    # reference, which is exactly what the SRS specifies.
    workspace_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    # The FK here is intentional and has no ondelete action (NO ACTION), so a
    # user who has acted on the platform cannot be hard-deleted — UC-18
    # suspends accounts (`users.status`) rather than deleting them.
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), index=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    target_entity: Mapped[str] = mapped_column(String(128), nullable=False)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSONVariant, nullable=False)
