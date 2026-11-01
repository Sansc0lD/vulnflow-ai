"""Tabel `proofs_of_concept` — SDD §2.4.2 #8. Enkripsi at-rest: §2.4.3."""

import uuid

from sqlalchemy import ForeignKey, Integer, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, JSONVariant


class ProofOfConcept(Base):
    __tablename__ = "proofs_of_concept"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    finding_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("findings.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    encrypted_raw_evidence: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    iv_nonce: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    auth_tag: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    # Supports master-key rotation (SDD §2.4.3) without breaking old rows.
    key_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    # A JSON *array* of ordered steps, matching `ProofOfConceptSchema
    # .reproduction_steps: list[str]`, which is what both ingestion paths
    # actually persist. Previously annotated `dict[str, Any] | None`: JSONB
    # accepts either shape so nothing failed at write time, but the declared
    # type contradicted the stored data, and SQLAlchemy's `**kw: Any`
    # constructor meant `mypy --strict` could not catch it at the call sites.
    reproduction_steps: Mapped[list[str] | None] = mapped_column(JSONVariant)
    # Array URL lampiran S3 privat (SDD §2.4.2 #8).
    attachment_file_urls: Mapped[list[str] | None] = mapped_column(JSONVariant)
