"""PLAN.md FASE 7.2 — EC-11: Triage Optimistic Locking with StaleDataError Mitigation.

EDGE_CASES_AND_RESILIENCE.md §6 item 11:
When two auditors concurrently review and modify the same finding's triage status,
a race condition (lost update) is prevented via SQLAlchemy optimistic locking
(`Finding.__mapper_args__["version_id_col"] = version`).
The second concurrent update matches zero rows and raises `StaleDataError`,
which translates into a clean HTTP 409 Conflict rather than silently overwriting.
"""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from app.models.base import Base
from app.models.finding import Finding
from app.models.project import Project
from app.models.workspace import Workspace
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError
from sqlalchemy.pool import StaticPool


def test_ec11_concurrent_updates_trigger_stale_data_error() -> None:
    """Simultaneous status edits on the same finding version result in StaleDataError."""
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)

    try:
        # Initial setup: create project and finding at version 1
        with Session(engine) as setup_session:
            workspace = Workspace(name="Agency")
            setup_session.add(workspace)
            setup_session.commit()

            project = Project(
                workspace_id=workspace.id,
                name="Triage Race Project",
                client_name="Client",
                target_scope="*.corp.com",
                roe_start_date=datetime(2026, 11, 1, tzinfo=UTC),
                roe_end_date=datetime(2026, 11, 10, tzinfo=UTC),
            )
            setup_session.add(project)
            setup_session.commit()

            finding = Finding(
                project_id=project.id,
                dedup_hash="dedup_race_hash",
                title="Race Condition SQLi",
                severity="CRITICAL",
                cvss_score=Decimal("9.8"),
                cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
                cwe_id="CWE-89",
                target_host="app.corp.com",
                source_tool="nuclei",
            )
            setup_session.add(finding)
            setup_session.commit()
            finding_id = finding.id
            assert finding.version == 1

        # Two auditors open the finding concurrently
        with Session(engine) as auditor_a, Session(engine) as auditor_b:
            f_a = auditor_a.get(Finding, finding_id)
            f_b = auditor_b.get(Finding, finding_id)
            assert f_a is not None and f_b is not None
            assert f_a.version == 1
            assert f_b.version == 1

            # Auditor A updates status to IN_REVIEW and commits first
            f_a.status = "IN_REVIEW"
            auditor_a.commit()
            assert f_a.version == 2

            # Auditor B attempts to mark as FALSE_POSITIVE based on outdated version 1
            f_b.status = "FALSE_POSITIVE"
            with pytest.raises(StaleDataError):
                auditor_b.commit()
            auditor_b.rollback()

        # Verify state in database remains Auditor A's commit, not overwritten
        with Session(engine) as check_session:
            current = check_session.get(Finding, finding_id)
            assert current is not None
            assert current.status == "IN_REVIEW"
            assert current.version == 2
    finally:
        engine.dispose()
