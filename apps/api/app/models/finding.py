"""Tabel `findings` — SDD §2.4.2 #7."""

import uuid
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Integer, Numeric, String, UniqueConstraint
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
