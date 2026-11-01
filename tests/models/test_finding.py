"""PLAN.md FASE 2.3 — Tabel `findings` (SDD §2.4.2 #7)."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from app.models.base import Base
from app.models.finding import Finding
from app.models.project import Project
from app.models.workspace import Workspace
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError
from sqlalchemy.pool import StaticPool


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


def test_finding_persists_created_at(session: Session) -> None:
    """`ManualFindingResponse.created_at` is a required contract field and
    UC-11 retest tracking needs a first-seen date; before this column the API
    fabricated a timestamp per request that was never stored.
    """
    project = _make_project(session)
    finding = Finding(
        project_id=project.id,
        dedup_hash="hash-created-at",
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

    assert finding.created_at is not None
    reloaded = session.query(Finding).filter_by(dedup_hash="hash-created-at").one()
    assert reloaded.created_at == finding.created_at


def test_concurrent_update_raises_stale_data_error() -> None:
    """EC-11 — the real optimistic lock.

    Comparing `version` in Python before the UPDATE is not a lock: two
    requests can both read version=1, both pass the comparison, and the
    second simply overwrites the first (lost update, both callers get 200).
    `Finding.__mapper_args__["version_id_col"]` makes the UPDATE carry
    `WHERE version = :old_version`, so the loser's statement matches 0 rows.

    StaticPool pins both Sessions to one SQLite connection so the two
    transactions see each other's committed state deterministically.
    """
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    try:
        with Session(engine) as setup:
            project = _make_project(setup)
            finding = Finding(
                project_id=project.id,
                dedup_hash="race",
                title="T",
                severity="LOW",
                cvss_score=Decimal("1.0"),
                cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:N",
                cwe_id="UNKNOWN",
                target_host="app.klien.com",
                source_tool="manual",
            )
            setup.add(finding)
            setup.commit()
            finding_id = finding.id

        with Session(engine) as auditor_a, Session(engine) as auditor_b:
            seen_by_a = auditor_a.get(Finding, finding_id)
            seen_by_b = auditor_b.get(Finding, finding_id)
            assert seen_by_a is not None and seen_by_b is not None
            assert seen_by_a.version == seen_by_b.version == 1

            seen_by_a.status = "REMEDIATED"
            auditor_a.commit()
            assert seen_by_a.version == 2  # bumped by SQLAlchemy, not by hand

            seen_by_b.status = "FALSE_POSITIVE"
            with pytest.raises(StaleDataError):
                auditor_b.commit()
    finally:
        engine.dispose()
