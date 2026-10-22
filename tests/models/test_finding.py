"""PLAN.md FASE 2.3 — Tabel `findings` (SDD §2.4.2 #7)."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from app.models.finding import Finding
from app.models.project import Project
from app.models.workspace import Workspace
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


def _make_project(session: Session) -> Project:
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
    return project


def test_create_finding_applies_defaults(session: Session) -> None:
    project = _make_project(session)

    finding = Finding(
        project_id=project.id,
        dedup_hash="hash1",
        title="SQL Injection",
        severity="CRITICAL",
        cvss_score=Decimal("9.8"),
        cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
        cwe_id="CWE-89",
        target_host="app.klien.com",
        source_tool="nuclei",
    )
    session.add(finding)
    session.commit()

    assert finding.endpoint_path == ""  # EC-08: dedup_hash component, never NULL
    assert finding.target_port is None  # EC-09: non-network findings have no port
    assert finding.status == "OPEN"
    assert finding.is_curated_for_report is True
    assert finding.is_quarantined is False
    assert finding.version == 1  # optimistic-locking counter (EC-11)
    assert finding.cvss_version == "3.1"
    assert finding.protocol == "tcp"


def test_finding_dedup_hash_must_be_unique(session: Session) -> None:
    project = _make_project(session)
    common_fields = {
        "project_id": project.id,
        "title": "Finding",
        "severity": "LOW",
        "cvss_score": Decimal("2.0"),
        "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:N",
        "cwe_id": "UNKNOWN",
        "target_host": "app.klien.com",
        "source_tool": "manual",
    }

    session.add(Finding(dedup_hash="dup-hash", **common_fields))
    session.commit()
    session.add(Finding(dedup_hash="dup-hash", **common_fields))

    with pytest.raises(IntegrityError):
        session.commit()
