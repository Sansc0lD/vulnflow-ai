"""PLAN.md FASE 2.3 — Tabel `users` (SDD §2.4.2 #1)."""

import pytest
from app.models.user import User
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


def test_create_user_applies_defaults(session: Session) -> None:
    user = User(
        email="auditor@example.com",
        password_hash="argon2id$...",
        full_name="Auditor Satu",
    )
    session.add(user)
    session.commit()

    assert user.id is not None
    assert user.token_version == 1
    assert user.status == "ACTIVE"
    assert user.created_at is not None


def test_user_email_must_be_unique(session: Session) -> None:
    session.add(User(email="dup@example.com", password_hash="h1", full_name="A"))
    session.commit()
    session.add(User(email="dup@example.com", password_hash="h2", full_name="B"))

    with pytest.raises(IntegrityError):
        session.commit()
