"""Unit tests — PLAN.md FASE 2.6: seeder akun admin & template paket langganan."""

from collections.abc import Generator

import pytest
from app.core.seeder import get_seed_admin_password, seed_defaults
from app.models.base import Base
from app.models.subscription import Subscription
from app.models.user import User
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember
from argon2 import PasswordHasher
from sqlalchemy import create_engine
from sqlalchemy.orm import Session


@pytest.fixture
def session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


@pytest.fixture(autouse=True)
def _seed_password_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SEED_ADMIN_PASSWORD", "Str0ng!SeedPassw0rd")


def test_seed_defaults_creates_admin_user(session: Session) -> None:
    seed_defaults(session)

    admin = session.query(User).filter_by(email="admin@vulnflow.local").one()
    assert admin.full_name == "VulnFlow Admin"
    PasswordHasher().verify(admin.password_hash, "Str0ng!SeedPassw0rd")


def test_seed_defaults_creates_free_and_pro_template_workspaces(session: Session) -> None:
    seed_defaults(session)

    free_sub = session.query(Subscription).filter_by(tier="FREE").one()
    pro_sub = session.query(Subscription).filter_by(tier="PRO").one()
    assert free_sub.monthly_report_quota == 3
    assert pro_sub.monthly_report_quota == 30


def test_seed_defaults_makes_admin_a_manager_of_both_template_workspaces(session: Session) -> None:
    seed_defaults(session)

    admin = session.query(User).filter_by(email="admin@vulnflow.local").one()
    memberships = session.query(WorkspaceMember).filter_by(user_id=admin.id).all()
    assert len(memberships) == 2
    assert all(m.role == "MANAGER" for m in memberships)


def test_seed_defaults_is_idempotent(session: Session) -> None:
    seed_defaults(session)
    seed_defaults(session)

    assert session.query(User).count() == 1
    assert session.query(Workspace).count() == 2
    assert session.query(Subscription).count() == 2


def test_get_seed_admin_password_raises_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SEED_ADMIN_PASSWORD", raising=False)

    with pytest.raises(RuntimeError, match="SEED_ADMIN_PASSWORD"):
        get_seed_admin_password()
