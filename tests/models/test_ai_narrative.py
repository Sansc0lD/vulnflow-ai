"""PLAN.md FASE 2.3 — Tabel `ai_narratives` (SDD §2.4.2 #9)."""

from datetime import UTC, datetime

from app.models.ai_narrative import AINarrative
from app.models.project import Project
from app.models.workspace import Workspace
from sqlalchemy.orm import Session


def test_create_ai_narrative_applies_defaults(session: Session) -> None:
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

    narrative = AINarrative(
        project_id=project.id,
        executive_summary="Ringkasan eksekutif.",
        business_impact="Dampak bisnis signifikan.",
        remediation_priorities=[{"cwe_id": "CWE-89", "priority": 1}],
    )
    session.add(narrative)
    session.commit()

    assert narrative.tokens_consumed == 0
    assert narrative.is_fallback is False  # EC-14 fallback flag
    assert narrative.approval_status == "DRAFT"
    assert narrative.generated_at is not None
