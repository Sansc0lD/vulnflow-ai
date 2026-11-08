"""PLAN.md FASE 7.2 — EC-17: S3 Presigned URL Dynamic Regeneration via HTTP 307.

EDGE_CASES_AND_RESILIENCE.md §5.4 & §6 item 17:
Static direct download URLs expire after 15 minutes, leaving clients with broken links.
The `/download` proxy endpoint dynamically mints a fresh presigned URL on every request
and issues an HTTP 307 (Temporary Redirect), while enforcing tenant workspace isolation.
"""

import uuid
from collections.abc import Generator
from datetime import UTC, datetime

import pytest
from app.core.exceptions import ResourceNotFoundError
from app.models.base import Base
from app.models.project import Project
from app.models.report import Report
from app.models.user import User
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember
from app.routers.reports import download_report
from sqlalchemy import create_engine
from sqlalchemy.orm import Session


class _FakeS3Storage:
    def __init__(self) -> None:
        self.calls: list[tuple[str, int]] = []

    def generate_presigned_url(self, storage_path: str, *, expires_in_seconds: int = 900) -> str:
        self.calls.append((storage_path, expires_in_seconds))
        return f"https://s3.amazonaws.com/vulnflow-bucket/{storage_path}?token={uuid.uuid4()}&expires={expires_in_seconds}"


@pytest.fixture
def session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s
    engine.dispose()


def test_ec17_download_proxy_dynamically_generates_fresh_url_with_307(session: Session) -> None:
    """Download proxy generates fresh presigned URL and returns HTTP 307 Redirect."""
    workspace = Workspace(name="Agency")
    user = User(email="viewer@agency.com", password_hash="hash", full_name="Viewer")
    session.add_all([workspace, user])
    session.commit()

    member = WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role="VIEWER")
    project = Project(
        workspace_id=workspace.id,
        name="Security Audit",
        client_name="Client Corp",
        target_scope="*.corp.com",
        roe_start_date=datetime(2026, 11, 1, tzinfo=UTC),
        roe_end_date=datetime(2026, 11, 10, tzinfo=UTC),
    )
    session.add_all([member, project])
    session.commit()

    storage_path = f"reports/{project.id}/final_report.pdf"
    report = Report(
        project_id=project.id,
        report_title="Final Assessment",
        storage_path=storage_path,
        watermark_applied=False,
    )
    session.add(report)
    session.commit()

    storage = _FakeS3Storage()

    # Call download_report
    redirect_resp = download_report(
        workspace_id=workspace.id,
        report_id=report.id,
        db=session,
        storage=storage,  # type: ignore[arg-type]
        _member=member,
    )

    assert redirect_resp.status_code == 307
    assert storage_path in redirect_resp.headers["location"]
    assert "token=" in redirect_resp.headers["location"]
    assert len(storage.calls) == 1
    assert storage.calls[0][1] == 900  # 15 minutes TTL


def test_ec17_download_proxy_rejects_cross_tenant_report_access(session: Session) -> None:
    """Attempting download of report from foreign workspace raises ResourceNotFoundError (404)."""
    w_a = Workspace(name="Workspace A")
    w_b = Workspace(name="Workspace B")
    session.add_all([w_a, w_b])
    session.commit()

    project_a = Project(
        workspace_id=w_a.id,
        name="Project A",
        client_name="Client A",
        target_scope="*.a.com",
        roe_start_date=datetime(2026, 11, 1, tzinfo=UTC),
        roe_end_date=datetime(2026, 11, 10, tzinfo=UTC),
    )
    session.add(project_a)
    session.commit()

    report_a = Report(
        project_id=project_a.id,
        report_title="Report A",
        storage_path="reports/a.pdf",
        watermark_applied=False,
    )
    session.add(report_a)
    session.commit()

    storage = _FakeS3Storage()
    member_b = WorkspaceMember(workspace_id=w_b.id, user_id=uuid.uuid4(), role="MANAGER")

    # Member in workspace B tries to access report belonging to workspace A
    with pytest.raises(ResourceNotFoundError, match="Report not found in this workspace"):
        download_report(
            workspace_id=w_b.id,
            report_id=report_a.id,
            db=session,
            storage=storage,  # type: ignore[arg-type]
            _member=member_b,
        )
