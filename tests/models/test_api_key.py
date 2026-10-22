"""PLAN.md FASE 2.3 — Tabel `api_keys` (SDD §2.4.2 #5)."""

import pytest
from app.models.api_key import APIKey
from app.models.user import User
from app.models.workspace import Workspace
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


def test_create_api_key_applies_defaults(session: Session) -> None:
    workspace = Workspace(name="Agensi")
    user = User(email="auditor@example.com", password_hash="h", full_name="A")
    session.add_all([workspace, user])
    session.commit()

    key = APIKey(
        workspace_id=workspace.id,
        created_by_user_id=user.id,
        key_hash="a" * 64,
        label="Laptop-Pentester-01",
    )
    session.add(key)
    session.commit()

    assert key.is_active is True
    assert key.last_used_at is None


def test_api_key_hash_must_be_unique(session: Session) -> None:
    workspace = Workspace(name="Agensi")
    user = User(email="auditor@example.com", password_hash="h", full_name="A")
    session.add_all([workspace, user])
    session.commit()

    session.add(
        APIKey(workspace_id=workspace.id, created_by_user_id=user.id, key_hash="b" * 64, label="X")
    )
    session.commit()
    session.add(
        APIKey(workspace_id=workspace.id, created_by_user_id=user.id, key_hash="b" * 64, label="Y")
    )

    with pytest.raises(IntegrityError):
        session.commit()
