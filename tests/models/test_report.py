"""PLAN.md FASE 2.3 — Tabel `reports` (SDD §2.4.2 #10)."""

from datetime import UTC, datetime

from app.models.project import Project
from app.models.report import Report
from app.models.workspace import Workspace
from sqlalchemy.orm import Session


def test_create_report_applies_defaults(session: Session) -> None:
    workspace = Workspace(name="Agensi")
    session.add(workspace)
    session.commit()
    project = Project(
        workspace_id=workspace.id,
        name="Audit",
        client_name="Klien",
        target_scope="*.klien.com",
        roe_start_date=datetime(2026, 10, 1, tzinfo=UTC),
        roe_end_date=datetime(2026, 11, 1, tzinfo=UTC),
    )
    session.add(project)
    session.commit()

    report = Report(
        project_id=project.id,
        report_title="Laporan Audit Keamanan Bank XYZ",
        storage_path="reports/prj_bank_audit/v1.0.pdf",
        watermark_applied=True,
    )
    session.add(report)
    session.commit()

    assert report.version == "v1.0"
    assert report.generated_at is not None
