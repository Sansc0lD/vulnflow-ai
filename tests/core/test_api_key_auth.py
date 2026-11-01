"""PLAN.md FASE 4.4 — API-key authentication for CLI ingestion (SDD §2.6.1.2)."""

from collections.abc import Generator

import pytest
from app.core.dependencies import authenticate_api_key
from app.core.exceptions import AuthenticationError
from app.core.security import generate_api_key
from app.models.api_key import APIKey
from app.models.base import Base
from app.models.user import User
from app.models.workspace import Workspace
from sqlalchemy import create_engine
from sqlalchemy.orm import Session


@pytest.fixture
def session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


def _make_api_key(session: Session, *, is_active: bool = True) -> tuple[str, Workspace]:
    user = User(email="auditor@example.com", password_hash="h", full_name="A")
    workspace = Workspace(name="Agensi")
    session.add_all([user, workspace])
    session.commit()
    raw_key, key_hash = generate_api_key()
    session.add(
        APIKey(
            workspace_id=workspace.id,
            created_by_user_id=user.id,
            key_hash=key_hash,
            label="CI",
            is_active=is_active,
        )
    )
    session.commit()
    return raw_key, workspace


def test_authenticate_api_key_returns_matching_workspace(session: Session) -> None:
    raw_key, workspace = _make_api_key(session)

    api_key = authenticate_api_key(raw_key, workspace.id, session)

    assert api_key.workspace_id == workspace.id


def test_authenticate_api_key_updates_last_used_at(session: Session) -> None:
    raw_key, workspace = _make_api_key(session)

    api_key = authenticate_api_key(raw_key, workspace.id, session)

    assert api_key.last_used_at is not None


def test_authenticate_api_key_rejects_unknown_key(session: Session) -> None:
    _, workspace = _make_api_key(session)

    with pytest.raises(AuthenticationError):
        authenticate_api_key("vf_live_does-not-exist", workspace.id, session)


def test_authenticate_api_key_rejects_inactive_key(session: Session) -> None:
    raw_key, workspace = _make_api_key(session, is_active=False)

    with pytest.raises(AuthenticationError):
        authenticate_api_key(raw_key, workspace.id, session)


def test_authenticate_api_key_rejects_wrong_workspace(session: Session) -> None:
    raw_key, _ = _make_api_key(session)
    other_workspace = Workspace(name="Agensi Lain")
    session.add(other_workspace)
    session.commit()

    with pytest.raises(AuthenticationError):
        authenticate_api_key(raw_key, other_workspace.id, session)
