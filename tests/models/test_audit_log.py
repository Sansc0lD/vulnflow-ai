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


def test_audit_log_survives_workspace_deletion(session: Session) -> None:
    """SRS UC-04 E2 step 2 / UC-19 E1 — audit rows are retained after a
    workspace is purged ("tidak di-cascade-delete") as platform compliance
    evidence, keeping `workspace_id` as a dangling historical reference.
    """
    workspace = Workspace(name="Agensi")
    session.add(workspace)
    session.commit()
    workspace_id = workspace.id
    session.add(
        AuditLog(
            workspace_id=workspace_id,
            action="WORKSPACE_PURGED",
            target_entity="workspaces",
            ip_address="203.0.113.10",
            details={"reason": "30-day retention elapsed"},
        )
    )
    session.commit()

    session.delete(workspace)
    session.commit()

    retained = session.query(AuditLog).filter_by(action="WORKSPACE_PURGED").one()
    assert retained.workspace_id == workspace_id
