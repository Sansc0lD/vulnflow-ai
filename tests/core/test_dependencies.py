"""PLAN.md FASE 4.1/4.2/4.3 — auth & RBAC dependency logic (pure, DB-backed)."""

import uuid
from collections.abc import Generator

import pytest
from app.core.dependencies import authenticate_user, ensure_workspace_role, workspace_is_active
from app.core.exceptions import AuthenticationError, PermissionDeniedError
from app.core.security import create_access_token
from app.models.base import Base
from app.models.user import User
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

_SECRET = "test-secret-key-at-least-32-bytes-long!"


@pytest.fixture
def session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


def _make_user(session: Session) -> User:
    user = User(email="auditor@example.com", password_hash="h", full_name="A")
    session.add(user)
    session.commit()
    return user


def test_authenticate_user_returns_user_for_valid_token(session: Session) -> None:
    user = _make_user(session)
    token = create_access_token(
        user_id=str(user.id),
        token_version=user.token_version,
        secret_key=_SECRET,
        algorithm="HS256",
        expires_in_seconds=3600,
    )

    result = authenticate_user(token, session, secret_key=_SECRET, algorithm="HS256")

    assert result.id == user.id


def test_authenticate_user_rejects_invalid_token(session: Session) -> None:
    with pytest.raises(AuthenticationError):
        authenticate_user("not-a-jwt", session, secret_key=_SECRET, algorithm="HS256")


def test_authenticate_user_rejects_unknown_user(session: Session) -> None:
    import uuid

    token = create_access_token(
        user_id=str(uuid.uuid4()),
        token_version=1,
        secret_key=_SECRET,
        algorithm="HS256",
        expires_in_seconds=3600,
    )

    with pytest.raises(AuthenticationError):
        authenticate_user(token, session, secret_key=_SECRET, algorithm="HS256")


def test_authenticate_user_rejects_revoked_token_version(session: Session) -> None:
    # Simulates logout-all / password change bumping token_version (SDD §2.6.1.4).
    user = _make_user(session)
    token = create_access_token(
        user_id=str(user.id),
        token_version=user.token_version,
        secret_key=_SECRET,
        algorithm="HS256",
        expires_in_seconds=3600,
    )
    user.token_version += 1
    session.commit()

    with pytest.raises(AuthenticationError):
        authenticate_user(token, session, secret_key=_SECRET, algorithm="HS256")


def test_authenticate_user_rejects_suspended_user(session: Session) -> None:
    # F4-HIGH-03: suspended users must not be authenticated
    user = _make_user(session)
    user.status = "SUSPENDED"
    session.commit()

    token = create_access_token(
        user_id=str(user.id),
        token_version=user.token_version,
        secret_key=_SECRET,
        algorithm="HS256",
        expires_in_seconds=3600,
    )

    with pytest.raises(AuthenticationError, match="suspended"):
        authenticate_user(token, session, secret_key=_SECRET, algorithm="HS256")


def test_revoke_user_tokens_invalidates_active_token(session: Session) -> None:
    from app.core.dependencies import revoke_user_tokens

    user = _make_user(session)
    token = create_access_token(
        user_id=str(user.id),
        token_version=user.token_version,
        secret_key=_SECRET,
        algorithm="HS256",
        expires_in_seconds=3600,
    )

    revoke_user_tokens(user, session)

    with pytest.raises(AuthenticationError, match="revoked"):
        authenticate_user(token, session, secret_key=_SECRET, algorithm="HS256")


def test_ensure_workspace_role_allows_permitted_role(session: Session) -> None:
    user = _make_user(session)
    workspace = Workspace(name="Agensi")
    session.add(workspace)
    session.commit()
    member = WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role="MANAGER")
    session.add(member)
    session.commit()

    result = ensure_workspace_role(member, allowed_roles={"MANAGER"})
    assert result is member


def test_ensure_workspace_role_rejects_unpermitted_role(session: Session) -> None:
    user = _make_user(session)
    workspace = Workspace(name="Agensi")
    session.add(workspace)
    session.commit()
    member = WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role="VIEWER")
    session.add(member)
    session.commit()

    with pytest.raises(PermissionDeniedError):
        ensure_workspace_role(member, allowed_roles={"MANAGER", "PENTESTER"})


def test_ensure_workspace_role_rejects_non_member() -> None:
    with pytest.raises(PermissionDeniedError):
        ensure_workspace_role(None, allowed_roles={"MANAGER"})


def test_workspace_is_active_rejects_soft_deleted_workspace(session: Session) -> None:
    """UC-04 — `workspaces.is_deleted` was written by nothing and read by
    nothing, so a soft-deleted workspace stayed fully readable and writable
    for its entire 30-day retention window.
    """
    live = Workspace(name="Agensi Aktif")
    deleted = Workspace(name="Agensi Dihapus", is_deleted=True)
    session.add_all([live, deleted])
    session.commit()

    assert workspace_is_active(live.id, session) is True
    assert workspace_is_active(deleted.id, session) is False


def test_workspace_is_active_rejects_unknown_workspace(session: Session) -> None:
    assert workspace_is_active(uuid.uuid4(), session) is False
