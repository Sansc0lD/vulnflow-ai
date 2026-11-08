"""PLAN.md FASE 7.2 — EC-09: Nullable Port Rendering for Non-Network Findings.

EDGE_CASES_AND_RESILIENCE.md §6 item 9:
Findings originating from non-network tools, cloud configurations, or web logic flaws
often have no associated network port (`target_port = None`).
Schemas, ORM models, deduplication hashing, and report rendering must cleanly
handle `None` without `TypeError`, rendering safely without crashing.
"""

from collections.abc import Generator
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from app.domain.deduplication import compute_dedup_hash
from app.models.base import Base
from app.models.finding import Finding
from app.models.project import Project
from app.models.workspace import Workspace
from app.services.report_renderer import build_report_html
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from vulnflow_contracts import (
    ProofOfConceptSchema,
    Protocol,
    Severity,
    SourceTool,
    UnifiedVulnerabilityFinding,
)


@pytest.fixture
def session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s
    engine.dispose()


def test_ec09_schema_and_dedup_hash_handle_none_port() -> None:
    """UnifiedVulnerabilityFinding and compute_dedup_hash accept None for port."""
    finding = UnifiedVulnerabilityFinding(
        title="AWS S3 Bucket Public Read",
        severity=Severity.HIGH,
        cwe_id="CWE-200",
        target_host="company-backups.s3.amazonaws.com",
        target_port=None,
        endpoint_path="",
        protocol=Protocol.OTHER,
        source_tool=SourceTool.MANUAL,
        proof_of_concept=ProofOfConceptSchema(raw_evidence="Bucket allows anonymous s3:GetObject"),
    )
    assert finding.target_port is None

    # Hashing does not raise TypeError when port is None
    dedup_hash = compute_dedup_hash(
        project_id="proj-1",
        cwe_id=finding.cwe_id,
        host=finding.target_host,
        port=finding.target_port,
        endpoint_path=finding.endpoint_path,
    )
    assert len(dedup_hash) == 64


def test_ec09_orm_and_report_html_render_null_port_safely(session: Session) -> None:
    """ORM persists target_port=None and build_report_html formats it safely."""
    workspace = Workspace(name="Cloud Agency")
    session.add(workspace)
    session.commit()

    project = Project(
        workspace_id=workspace.id,
        name="Cloud Security Review",
        client_name="Cloud Corp",
        target_scope="*.s3.amazonaws.com",
        roe_start_date=datetime(2026, 11, 1, tzinfo=UTC),
        roe_end_date=datetime(2026, 11, 10, tzinfo=UTC),
    )
    session.add(project)
    session.commit()

    orm_finding = Finding(
        project_id=project.id,
        dedup_hash="hash_null_port_1",
        title="Missing CloudTrail Logging",
        severity="MEDIUM",
        cvss_score=Decimal("5.3"),
        cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N",
        cwe_id="CWE-778",
        target_host="management-console",
        target_port=None,  # Nullable port
        endpoint_path="",
        source_tool="manual",
    )
    session.add(orm_finding)
    session.commit()

    # Query back to verify None is persisted
    fetched = session.get(Finding, orm_finding.id)
    assert fetched is not None
    assert fetched.target_port is None

    # Render HTML report containing this finding dictionary
    html = build_report_html(
        report_title="Cloud Security Assessment",
        client_name=project.client_name,
        findings=[
            {
                "title": fetched.title,
                "severity": fetched.severity,
                "cvss_score": fetched.cvss_score,
                "cwe_id": fetched.cwe_id,
                "port": fetched.target_port,
            }
        ],
        executive_summary="Summary text.",
        business_impact="Impact text.",
        watermark_text=None,
    )
    assert "Missing CloudTrail Logging" in html
    assert "<html>" in html
