"""PLAN.md FASE 2.3 — Tabel `audit_logs` (SDD §2.4.2 #11, partisi bulanan §2.4.4)."""

from app.models.audit_log import AuditLog
from app.models.user import User
from app.models.workspace import Workspace
from sqlalchemy.orm import Session


def test_create_audit_log_applies_defaults(session: Session) -> None:
    workspace = Workspace(name="Agensi")
    user = User(email="auditor@example.com", password_hash="h", full_name="A")
    session.add_all([workspace, user])
    session.commit()

    log = AuditLog(
        workspace_id=workspace.id,
        actor_user_id=user.id,
        action="LOGIN",
        target_entity="workspaces",
        ip_address="203.0.113.10",
        details={"reason": "successful login"},
    )
    session.add(log)
    session.commit()

    assert log.id is not None
    assert log.created_at is not None


def test_audit_log_actor_user_id_is_nullable(session: Session) -> None:
    workspace = Workspace(name="Agensi")
    session.add(workspace)
    session.commit()

    log = AuditLog(
        workspace_id=workspace.id,
        actor_user_id=None,
        action="SYSTEM_CLEANUP",
        target_entity="subscriptions",
        ip_address="0.0.0.0",
        details={},
    )
    session.add(log)
    session.commit()

    assert log.actor_user_id is None
