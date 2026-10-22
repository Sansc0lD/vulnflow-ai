"""Tabel `workspaces` — SDD §2.4.2 #2."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    custom_logo_url: Mapped[str | None] = mapped_column(String(500))
    brand_primary_color: Mapped[str] = mapped_column(String(7), default="#0F172A")
    brand_secondary_color: Mapped[str] = mapped_column(String(7), default="#3B82F6")
    confidentiality_text: Mapped[str | None] = mapped_column(Text)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
