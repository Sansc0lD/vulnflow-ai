"""PLAN.md FASE 2.3 — Tabel `workspace_members` (SDD §2.4.2 #3)."""

import pytest
from app.models.user import User
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


def _make_workspace_and_user(session: Session) -> tuple[Workspace, User]:
    workspace = Workspace(name="Agensi")
    user = User(email="pentester@example.com", password_hash="h", full_name="P")
    session.add_all([workspace, user])
    session.commit()
    return workspace, user


def test_create_workspace_member_with_role(session: Session) -> None:
    workspace, user = _make_workspace_and_user(session)

    member = WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role="MANAGER")
    session.add(member)
    session.commit()

    assert member.id is not None
    assert member.role == "MANAGER"


def test_workspace_member_rejects_duplicate_membership(session: Session) -> None:
    workspace, user = _make_workspace_and_user(session)
    session.add(WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role="PENTESTER"))
    session.commit()

    session.add(WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role="VIEWER"))
    with pytest.raises(IntegrityError):
        session.commit()


def test_deleting_workspace_cascades_to_members(session: Session) -> None:
    workspace, user = _make_workspace_and_user(session)
    session.add(WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role="VIEWER"))
    session.commit()

    session.delete(workspace)
    session.commit()

    assert session.query(WorkspaceMember).count() == 0


def test_deleting_user_with_membership_is_rejected(session: Session) -> None:
    """EC-03 — SDD §2.7.1 requires the database to *reject* deleting an
    account before ownership is transferred. Under ON DELETE CASCADE the
    DELETE succeeded and took the membership with it, leaving a workspace
    with zero members that no one could reach but which still held its
    projects, findings and encrypted PoCs.
    """
    workspace, user = _make_workspace_and_user(session)
    session.add(WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role="MANAGER"))
    session.commit()

    session.delete(user)
    with pytest.raises(IntegrityError):
        session.commit()
