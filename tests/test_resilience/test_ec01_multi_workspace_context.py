"""PLAN.md FASE 7.2 — EC-01: Multi-Workspace Context Confusion.

SRS UC-03 & EDGE_CASES_AND_RESILIENCE.md §6 item 1:
Pentesters who belong to multiple workspaces must not leak or push findings
into the wrong workspace. The local CLI reads `active_workspace_id` explicitly
from config, and the backend RBAC strictly denies access (PermissionDeniedError)
if a user attempts an action against a workspace where they lack membership.
"""

import uuid
from collections.abc import Generator

import pytest
from app.core.dependencies import ensure_workspace_role
from app.core.exceptions import PermissionDeniedError
from app.models.base import Base
from app.models.user import User
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from vulnflow.config import CLIConfig, load_config, save_config


@pytest.fixture
def session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s
    engine.dispose()


def test_ec01_cli_config_persists_and_binds_explicit_active_workspace(tmp_path) -> None:
    """CLI strictly enforces active_workspace_id in config to prevent context confusion."""
    config_file = tmp_path / "config.json"
    w1_id = str(uuid.uuid4())
    cfg = CLIConfig(
        api_url="http://localhost:8000", api_key="vf_key_test", active_workspace_id=w1_id
    )
    save_config(cfg, path=config_file)

    loaded = load_config(path=config_file)
    assert loaded.active_workspace_id == w1_id
    assert loaded.api_url == "http://localhost:8000"


def test_ec01_backend_denies_access_when_user_targets_non_member_workspace(
    session: Session,
) -> None:
    """User who is a member of Workspace A has no membership in Workspace B."""
    user = User(email="pentester@agency.com", password_hash="dummy", full_name="Auditor")
    w_a = Workspace(name="Workspace Alpha")
    w_b = Workspace(name="Workspace Beta (Forbidden)")
    session.add_all([user, w_a, w_b])
    session.commit()

    # User belongs to Workspace A only
    session.add(WorkspaceMember(workspace_id=w_a.id, user_id=user.id, role="PENTESTER"))
    session.commit()

    # Query membership in Workspace B -> None
    member_b = (
        session.query(WorkspaceMember).filter_by(workspace_id=w_b.id, user_id=user.id).one_or_none()
    )
    assert member_b is None

    # ensure_workspace_role must raise PermissionDeniedError
    with pytest.raises(PermissionDeniedError, match="do not have access"):
        ensure_workspace_role(member_b, allowed_roles={"MANAGER", "PENTESTER"})
