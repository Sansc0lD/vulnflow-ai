"""PLAN.md FASE 7.2 — EC-03: Orphan Workspace Prevention.

SRS UC-04 E2 & EDGE_CASES_AND_RESILIENCE.md §6 item 3:
Deleting a user account that owns/manages a workspace is strictly prohibited
before transferring ownership. At the database layer, `workspace_members.user_id`
has NO ACTION (not CASCADE), so a raw delete raises IntegrityError rather
than leaving an orphaned workspace with zero members.
"""

from collections.abc import Generator

import pytest
from app.models.base import Base
from app.models.user import User
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


@pytest.fixture
def session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s
    engine.dispose()


def test_ec03_deleting_sole_owner_is_rejected_by_foreign_key_constraint(
    session: Session,
) -> None:
    """Deleting user with an active workspace membership fails, preventing orphaned workspaces."""
    workspace = Workspace(name="Critical Agency Workspace")
    owner = User(email="owner@agency.com", password_hash="hash", full_name="Sole Owner")
    session.add_all([workspace, owner])
    session.commit()

    membership = WorkspaceMember(workspace_id=workspace.id, user_id=owner.id, role="MANAGER")
    session.add(membership)
    session.commit()

    # Attempting to delete the owner directly must violate FK constraint
    session.delete(owner)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()

    # Workspace still exists intact with its owner and membership
    assert session.get(Workspace, workspace.id) is not None
    assert session.query(WorkspaceMember).filter_by(workspace_id=workspace.id).count() == 1


def test_ec03_deleting_workspace_cascades_safely_to_membership(session: Session) -> None:
    """Deleting the workspace itself cascades to memberships without orphaning."""
    workspace = Workspace(name="Purged Workspace")
    owner = User(email="owner2@agency.com", password_hash="hash", full_name="Owner Two")
    session.add_all([workspace, owner])
    session.commit()

    session.add(WorkspaceMember(workspace_id=workspace.id, user_id=owner.id, role="MANAGER"))
    session.commit()

    # Deleting workspace is allowed and cascades cleanly
    session.delete(workspace)
    session.commit()

    assert session.get(Workspace, workspace.id) is None
    assert session.query(WorkspaceMember).filter_by(workspace_id=workspace.id).count() == 0
    # User account remains unharmed
    assert session.get(User, owner.id) is not None
