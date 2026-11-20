"""Tabel `users` — SDD §2.4.2 #1."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (CheckConstraint("status IN ('ACTIVE', 'SUSPENDED')", name="ck_user_status"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    token_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", nullable=False)
    is_superadmin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    totp_secret: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


# A plain UNIQUE index on `email` is case-SENSITIVE under PostgreSQL's default
# collation (`'Alice@corp.com' = 'alice@corp.com'` is false), so on its own it
# would happily let one mailbox register twice and make login depend on the
# casing the user happened to type. This functional index is what actually
# enforces one-account-per-mailbox at the database level; the plain unique
# index on the column is kept alongside it (not redundant) because the planner
# cannot use a `lower(email)` index to satisfy the `email = :email` equality
# lookup performed on every login. Declared outside the class body so it can
# reference the mapped column itself rather than a string literal.
Index("uq_users_email_lower", func.lower(User.email), unique=True)
