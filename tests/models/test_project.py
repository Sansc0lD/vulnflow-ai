"""PLAN.md FASE 2.3 — Tabel `projects` (SDD §2.4.2 #6)."""

from datetime import UTC, datetime

from app.models.project import Project
from app.models.workspace import Workspace
from sqlalchemy.orm import Session


def test_create_project_applies_defaults(session: Session) -> None:
    workspace = Workspace(name="Agensi")
    session.add(workspace)
    session.commit()

    project = Project(
        workspace_id=workspace.id,
        name="Audit Bank XYZ",
        client_name="Bank XYZ",
        target_scope="*.bankxyz.co.id, 10.20.0.0/24",
        roe_start_date=datetime(2026, 10, 1, tzinfo=UTC),
        roe_end_date=datetime(2026, 11, 1, tzinfo=UTC),
    )
    session.add(project)
    session.commit()

    assert project.status == "ACTIVE"
    assert project.timezone == "UTC"
    assert project.lead_pentester_id is None
