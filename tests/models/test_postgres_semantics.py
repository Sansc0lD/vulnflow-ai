"""PostgreSQL-only guarantees that the SQLite unit lane cannot verify.

Two gaps motivate this module:

1. `DateTime(timezone=True)` is TIMESTAMPTZ on PostgreSQL (aware in, aware
   out) but SQLite has no timezone-aware storage and silently drops `tzinfo`.
   Every EC-05 ROE-expiry comparison therefore runs against *different*
   semantics in tests than in production, where `datetime.utcnow() >
   project.roe_end_date` raises `TypeError: can't compare offset-naive and
   offset-aware datetimes`.
2. The Alembic migrations were never executed by any test — the SQLite lanes
   build their schema with `Base.metadata.create_all`, so raw-DDL constructs
   (the `audit_logs` partitions) and model/migration drift were invisible.

This module runs `alembic downgrade base && alembic upgrade head` against a
real database, so it is opt-in:

    TEST_DATABASE_URL=postgresql+psycopg://vulnflow:<pw>@127.0.0.1:5432/vulnflow_test \
        uv run pytest tests/models/test_postgres_semantics.py

Point it at a THROWAWAY database — the fixture drops and rebuilds the schema.
"""

import os
import uuid
from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from app.models.audit_log import AuditLog
from app.models.finding import Finding
from app.models.project import Project
from app.models.user import User
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

_PG_URL = os.environ.get("TEST_DATABASE_URL", "")
_ALEMBIC_INI = Path(__file__).resolve().parents[2] / "apps" / "api" / "alembic.ini"

pytestmark = [
    pytest.mark.postgres,
    pytest.mark.skipif(
        not _PG_URL, reason="set TEST_DATABASE_URL to a throwaway PostgreSQL database"
    ),
]


@pytest.fixture(scope="module")
def engine() -> Generator[Engine, None, None]:
    from alembic import command
    from alembic.config import Config

    os.environ["DATABASE_URL"] = _PG_URL
    engine = create_engine(_PG_URL)
    # Reset by dropping the schema rather than by `downgrade base`: once an
    # audit row has outlived a purged workspace, the pre-fix schema can no
    # longer represent it and the downgrade refuses on purpose (see
    # d4a7f1c93b28). Dropping the schema also proves the migration builds the
    # whole database from nothing, which is the path production will take.
    with engine.begin() as connection:
        connection.execute(text("DROP SCHEMA public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))

    command.upgrade(Config(str(_ALEMBIC_INI)), "head")

    yield engine
    engine.dispose()


@pytest.fixture
def session(engine: Engine) -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
        session.rollback()


def _make_workspace(session: Session) -> Workspace:
    workspace = Workspace(name=f"Agensi {uuid.uuid4()}")
    session.add(workspace)
    session.commit()
    return workspace


def _make_project(session: Session) -> Project:
    project = Project(
        workspace_id=_make_workspace(session).id,
        name="Audit",
        client_name="Klien",
        target_scope="*.klien.com",
        roe_start_date=datetime(2026, 10, 1, tzinfo=UTC),
        roe_end_date=datetime(2026, 11, 1, tzinfo=UTC),
    )
    session.add(project)
    session.commit()
    return project


def _make_finding(session: Session, *, dedup_hash: str) -> Finding:
    finding = Finding(
        project_id=_make_project(session).id,
        dedup_hash=dedup_hash,
        title="T",
        severity="LOW",
        cvss_score=Decimal("1.0"),
        cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:N",
        cwe_id="UNKNOWN",
        target_host="app.klien.com",
        source_tool="manual",
    )
    session.add(finding)
    session.commit()
    return finding


# --- timezone semantics ----------------------------------------------------


def test_timestamptz_columns_return_aware_datetimes(session: Session) -> None:
    project = _make_project(session)
    session.expire_all()

    reloaded = session.get(Project, project.id)
    assert reloaded is not None
    assert reloaded.roe_end_date.tzinfo is not None, "TIMESTAMPTZ must round-trip tz-aware"
    # The comparison that silently works on naive SQLite values and is the one
    # EC-05 depends on.
    assert datetime.now(UTC) - reloaded.roe_end_date < timedelta(days=400)


def test_finding_created_at_is_server_generated_and_aware(session: Session) -> None:
    finding = _make_finding(session, dedup_hash=f"created-at-{uuid.uuid4()}")
    session.expire_all()

    reloaded = session.get(Finding, finding.id)
    assert reloaded is not None
    assert reloaded.created_at.tzinfo is not None


# --- schema invariants the review fixed ------------------------------------


def test_audit_logs_has_no_workspace_foreign_key(session: Session) -> None:
    """SRS UC-04 E2 / UC-19 E1 — audit rows outlive their workspace."""
    constraints = session.execute(
        text(
            "SELECT conname FROM pg_constraint "
            "WHERE conrelid = 'audit_logs'::regclass AND contype = 'f'"
        )
    ).scalars()

    assert "audit_logs_workspace_id_fkey" not in set(constraints)


def test_audit_log_row_survives_workspace_delete(session: Session) -> None:
    workspace_id = _make_workspace(session).id
    session.add(
        AuditLog(
            workspace_id=workspace_id,
            action="WORKSPACE_PURGED",
            target_entity="workspaces",
            ip_address="203.0.113.10",
            details={"reason": "retention elapsed"},
        )
    )
    session.commit()

    session.execute(text("DELETE FROM workspaces WHERE id = :wid"), {"wid": workspace_id})
    session.commit()
    # The Workspace instance is gone; drop it from the identity map so the
    # assertion below queries the database instead of refreshing a dead row.
    session.expunge_all()

    assert session.query(AuditLog).filter_by(workspace_id=workspace_id).count() == 1


def test_monthly_audit_log_partition_can_be_provisioned(session: Session) -> None:
    """The DEFAULT partition must never block `CREATE TABLE ... PARTITION OF`.

    With rows sitting in `audit_logs_default`, PostgreSQL aborts partition
    creation with "updated partition constraint for default partition would be
    violated by some row" — which is why `create_audit_log_partition()`
    relocates them first.
    """
    workspace = _make_workspace(session)
    far_future = datetime(2031, 7, 15, 12, 0, tzinfo=UTC)
    session.add(
        AuditLog(
            workspace_id=workspace.id,
            created_at=far_future,
            action="LOGIN",
            target_entity="workspaces",
            ip_address="203.0.113.10",
            details={},
        )
    )
    session.commit()

    created = session.execute(
        text("SELECT create_audit_log_partition(:month)"), {"month": far_future.date()}
    ).scalar_one()
    session.commit()

    assert created == "audit_logs_y2031m07"
    relocated = session.execute(
        text("SELECT count(*) FROM audit_logs_y2031m07 WHERE workspace_id = :wid"),
        {"wid": workspace.id},
    ).scalar_one()
    assert relocated == 1, "row must be moved out of the default partition, not lost"


def test_email_uniqueness_is_case_insensitive(session: Session) -> None:
    local = uuid.uuid4().hex
    session.add(User(email=f"{local}@corp.com", password_hash="h", full_name="A"))
    session.commit()
    session.add(User(email=f"{local.upper()}@CORP.com", password_hash="h", full_name="B"))

    with pytest.raises(IntegrityError):
        session.commit()


def test_deleting_user_with_membership_is_rejected(session: Session) -> None:
    """EC-03 — the database refuses, instead of orphaning the workspace."""
    workspace = _make_workspace(session)
    user = User(email=f"{uuid.uuid4().hex}@corp.com", password_hash="h", full_name="A")
    session.add(user)
    session.commit()
    session.add(WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role="MANAGER"))
    session.commit()

    with pytest.raises(IntegrityError):
        session.execute(text("DELETE FROM users WHERE id = :uid"), {"uid": user.id})
        session.commit()


def test_lead_pentester_is_nulled_when_user_is_deleted(session: Session) -> None:
    project = _make_project(session)
    user = User(email=f"{uuid.uuid4().hex}@corp.com", password_hash="h", full_name="Lead")
    session.add(user)
    session.commit()
    project.lead_pentester_id = user.id
    session.commit()

    session.execute(text("DELETE FROM users WHERE id = :uid"), {"uid": user.id})
    session.commit()
    session.expire_all()

    reloaded = session.get(Project, project.id)
    assert reloaded is not None
    assert reloaded.lead_pentester_id is None


def test_midtrans_order_id_is_unique(session: Session) -> None:
    indexes = session.execute(
        text(
            "SELECT indexdef FROM pg_indexes "
            "WHERE tablename = 'subscriptions' AND indexname = :name"
        ),
        {"name": "ix_subscriptions_midtrans_order_id"},
    ).scalar_one()

    assert "UNIQUE" in indexes


def test_no_redundant_duplicate_indexes(session: Session) -> None:
    """A unique constraint plus a separate plain index on the same column
    yields two btree indexes in PostgreSQL — write cost for no benefit.
    """
    duplicates = session.execute(
        text(
            "SELECT tablename, indexdef_cols, count(*) FROM ("
            "  SELECT tablename,"
            "         regexp_replace(indexdef, '^.*USING btree ', '') AS indexdef_cols"
            "    FROM pg_indexes WHERE schemaname = current_schema()"
            ") s GROUP BY tablename, indexdef_cols HAVING count(*) > 1"
        )
    ).all()

    assert duplicates == []


def test_schema_matches_models_after_migration(engine: Engine) -> None:
    """Guards against model/migration drift, which no other test could see:
    the SQLite lanes build their schema from `Base.metadata` directly and
    never run a migration at all.
    """
    from alembic.autogenerate import compare_metadata
    from alembic.migration import MigrationContext
    from app.core.migration_filters import load_partition_names, make_include_object
    from app.models import Base

    with engine.connect() as connection:
        context = MigrationContext.configure(
            connection,
            opts={"include_object": make_include_object(load_partition_names(connection))},
        )
        diff = compare_metadata(context, Base.metadata)

    assert diff == [], f"models and migrations have drifted: {diff}"
