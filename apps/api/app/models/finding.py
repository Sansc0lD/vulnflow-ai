"""Tabel `findings` — SDD §2.4.2 #7."""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Finding(Base):
    __tablename__ = "findings"
    __table_args__ = (
        UniqueConstraint("dedup_hash", name="uq_finding_dedup"),
        CheckConstraint(
            "severity IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO')",
            name="ck_finding_severity",
        ),
        CheckConstraint(
            "status IN ('OPEN', 'IN_REVIEW', 'REMEDIATED', 'REOPENED', "
            "'FALSE_POSITIVE', 'ACCEPTED_RISK')",
            name="ck_finding_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # SHA256(project_id + cwe_id + host + port + endpoint_path) — see EC-08 §5.2.
    # No index=True here: the UniqueConstraint below already backs this column
    # with a unique btree index — adding a second plain index would duplicate
    # it for no benefit while still paying its write cost on every insert.
    dedup_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    cvss_score: Mapped[Decimal] = mapped_column(Numeric(3, 1), nullable=False)
    cvss_version: Mapped[str] = mapped_column(String(10), default="3.1", nullable=False)
    cvss_vector: Mapped[str] = mapped_column(String(150), nullable=False)
    cwe_id: Mapped[str] = mapped_column(String(20), nullable=False)
    target_host: Mapped[str] = mapped_column(String(255), nullable=False)
    target_port: Mapped[int | None] = mapped_column(Integer)  # EC-09: nullable for non-network
    # Dedup_hash component, prevents over-deduplication across endpoints (EC-08).
    endpoint_path: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    protocol: Mapped[str] = mapped_column(String(10), default="tcp", nullable=False)
    source_tool: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="OPEN", nullable=False)
    is_curated_for_report: Mapped[bool] = mapped_column(default=True, nullable=False)
    # Target outside project.target_scope (UC-07d / EC-04).
    is_quarantined: Mapped[bool] = mapped_column(default=False, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)  # EC-11
    # First-seen timestamp. Required by `ManualFindingResponse.created_at` and
    # by UC-11 retest/regression tracking; without it the API had to invent a
    # value per request that was never persisted and could never be read back.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # EC-11 optimistic locking. Comparing `version` in Python before the UPDATE
    # is not a lock: under PostgreSQL's default READ COMMITTED two concurrent
    # triage requests both read version=1, both pass the comparison, and the
    # second UPDATE simply overwrites the first once the row lock is released
    # (lost update, both callers get HTTP 200). Registering the column as
    # `version_id_col` makes SQLAlchemy emit
    #   UPDATE findings SET ... WHERE id = :id AND version = :old_version
    # and raise StaleDataError when that matches 0 rows, which is the only
    # thing that actually makes the race impossible. SQLAlchemy also owns the
    # increment from here on, so callers must NOT bump `version` by hand.
    __mapper_args__ = {"version_id_col": version}
