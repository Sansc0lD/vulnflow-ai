"""Seeder data default — PLAN.md FASE 2.6: akun admin & template paket Free/Pro."""

import os
from datetime import UTC, datetime, timedelta

from argon2 import PasswordHasher
from sqlalchemy.orm import Session

from app.models.subscription import Subscription
from app.models.user import User
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember

ADMIN_EMAIL = "admin@vulnflow.local"
FREE_WORKSPACE_NAME = "VulnFlow Internal (Free Tier Template)"
PRO_WORKSPACE_NAME = "VulnFlow Internal (Pro Tier Template)"


def get_seed_admin_password() -> str:
    password = os.environ.get("SEED_ADMIN_PASSWORD")
    if not password:
        raise RuntimeError("SEED_ADMIN_PASSWORD environment variable is not set.")
    return password


def _get_or_create_admin(session: Session) -> User:
    admin = session.query(User).filter_by(email=ADMIN_EMAIL).one_or_none()
    if admin is not None:
        return admin
    admin = User(
        email=ADMIN_EMAIL,
        password_hash=PasswordHasher().hash(get_seed_admin_password()),
        full_name="VulnFlow Admin",
    )
    session.add(admin)
    session.flush()
    return admin


def _get_or_create_workspace_with_subscription(
    session: Session, admin: User, *, name: str, tier: str, monthly_report_quota: int
) -> None:
    if session.query(Workspace).filter_by(name=name).first() is not None:
        return
    workspace = Workspace(name=name)
    session.add(workspace)
    session.flush()
    session.add(WorkspaceMember(workspace_id=workspace.id, user_id=admin.id, role="MANAGER"))
    session.add(
        Subscription(
            workspace_id=workspace.id,
            tier=tier,
            monthly_report_quota=monthly_report_quota,
            quota_reset_date=datetime.now(UTC) + timedelta(days=30),
        )
    )


def seed_defaults(session: Session) -> None:
    admin = _get_or_create_admin(session)
    _get_or_create_workspace_with_subscription(
        session, admin, name=FREE_WORKSPACE_NAME, tier="FREE", monthly_report_quota=3
    )
    _get_or_create_workspace_with_subscription(
        session, admin, name=PRO_WORKSPACE_NAME, tier="PRO", monthly_report_quota=30
    )
    session.commit()
