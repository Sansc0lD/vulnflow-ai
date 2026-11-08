"""PLAN.md FASE 7.2 — EC-12: False Positive Report Exclusion.

EDGE_CASES_AND_RESILIENCE.md §6 item 12:
When a vulnerability finding is triaged and marked as `FALSE_POSITIVE`, it must
never remain checked or curated for final client audit report compilation.
The backend automatically resets `is_curated_for_report = False`.
"""

from collections.abc import Generator
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from app.models.base import Base
from app.models.finding import Finding
from app.models.project import Project
from app.models.user import User
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember
from app.routers.triage import update_finding_status
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from starlette.datastructures import Headers
from starlette.requests import Request

from vulnflow_contracts import FindingStatus, UpdateFindingStatusRequest


@pytest.fixture
def session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s
    engine.dispose()


def test_ec12_triage_marking_false_positive_unchecks_curated_for_report(session: Session) -> None:
    """Marking finding as FALSE_POSITIVE automatically sets is_curated_for_report to False."""
    workspace = Workspace(name="Audit Agency")
    user = User(email="auditor@agency.com", password_hash="h", full_name="Auditor")
    session.add_all([workspace, user])
    session.commit()

    member = WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role="PENTESTER")
    project = Project(
        workspace_id=workspace.id,
        name="Pentest",
        client_name="Target Corp",
        target_scope="*.target.com",
        roe_start_date=datetime(2026, 11, 1, tzinfo=UTC),
        roe_end_date=datetime(2026, 11, 10, tzinfo=UTC),
    )
    session.add_all([member, project])
    session.commit()

    finding = Finding(
        project_id=project.id,
        dedup_hash="hash_fp_1",
        title="Potential XSS on Search",
        severity="MEDIUM",
        cvss_score=Decimal("6.1"),
        cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N",
        cwe_id="CWE-79",
        target_host="target.com",
        source_tool="manual",
        status="OPEN",
        is_curated_for_report=True,  # Initially curated for report
        version=1,
    )
    session.add(finding)
    session.commit()
    assert finding.is_curated_for_report is True

    # Call update_finding_status
    scope = {
        "type": "http",
        "method": "PATCH",
        "path": (
            f"/api/v1/workspaces/{workspace.id}/projects/{project.id}/findings/{finding.id}/status"
        ),
        "headers": Headers({"client": "127.0.0.1"}).raw,
        "client": ("127.0.0.1", 50000),
    }
    dummy_request = Request(scope)

    update_payload = UpdateFindingStatusRequest(
        status=FindingStatus.FALSE_POSITIVE,
        version=1,
    )

    resp = update_finding_status(
        workspace_id=workspace.id,
        project_id=project.id,
        finding_id=finding.id,
        payload=update_payload,
        request=dummy_request,
        current_member=member,
        db=session,
    )

    assert resp.status == "FALSE_POSITIVE"
    assert resp.is_curated_for_report is False

    # Check database state directly
    refreshed = session.get(Finding, finding.id)
    assert refreshed is not None
    assert refreshed.status == "FALSE_POSITIVE"
    assert refreshed.is_curated_for_report is False
