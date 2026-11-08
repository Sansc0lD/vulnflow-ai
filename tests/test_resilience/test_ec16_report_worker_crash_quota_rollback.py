"""PLAN.md FASE 7.2 — EC-16: Report Worker Crash (PDF Bomb/OOM) Quota Protection.

EDGE_CASES_AND_RESILIENCE.md §5.3 & §6 item 16:
If the WeasyPrint engine crashes, runs out of memory (OOM), or encounters a malicious
CSS/HTML "PDF bomb", the compilation task aborts cleanly.
The platform guarantees that the client's monthly report quota is NOT deducted,
no phantom Report database records are committed, and no orphaned S3 objects linger.
"""

from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from app.models.base import Base
from app.models.finding import Finding
from app.models.project import Project
from app.models.report import Report
from app.models.subscription import Subscription
from app.models.workspace import Workspace
from app.workers.report_worker import compile_report
from sqlalchemy import create_engine
from sqlalchemy.orm import Session


class _FakeStorage:
    def __init__(self) -> None:
        self.files: dict[str, bytes] = {}

    def upload_bytes(self, path: str, data: bytes) -> None:
        self.files[path] = data

    def delete_file(self, path: str) -> None:
        self.files.pop(path, None)


def _cashing_render_fn(html: str) -> bytes:
    raise MemoryError("WeasyPrint worker killed: Out of Memory (OOM / PDF bomb).")


@pytest.fixture
def session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s
    engine.dispose()


def test_ec16_worker_crash_preserves_quota_and_commits_no_report(session: Session) -> None:
    """A rendering crash leaves reports_used_this_month unchanged and creates no Report."""
    workspace = Workspace(name="Target Agency")
    session.add(workspace)
    session.commit()

    sub = Subscription(
        workspace_id=workspace.id,
        tier="PRO",
        monthly_report_quota=30,
        reports_used_this_month=5,
        quota_reset_date=datetime.now(UTC) + timedelta(days=30),
    )
    project = Project(
        workspace_id=workspace.id,
        name="Mission Critical Pentest",
        client_name="Corp",
        target_scope="*.corp.com",
        roe_start_date=datetime(2026, 11, 1, tzinfo=UTC),
        roe_end_date=datetime(2026, 11, 10, tzinfo=UTC),
    )
    session.add_all([sub, project])
    session.commit()

    finding = Finding(
        project_id=project.id,
        dedup_hash="hash_crash_test",
        title="Complex Layout Finding",
        severity="HIGH",
        cvss_score=Decimal("8.0"),
        cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N",
        cwe_id="CWE-79",
        target_host="app.corp.com",
        source_tool="manual",
        is_curated_for_report=True,
    )
    session.add(finding)
    session.commit()

    storage = _FakeStorage()

    # Trigger compile_report with the crashing render function
    with pytest.raises(MemoryError, match="Out of Memory"):
        compile_report(
            session,
            storage,
            workspace_id=workspace.id,
            project_id=project.id,
            report_title="Annual Audit Report",
            executive_summary="Summary",
            business_impact="Impact",
            watermark_text=None,
            render_fn=_cashing_render_fn,
        )

    # Verify no Report row was committed
    assert session.query(Report).count() == 0
    # Verify no S3 object was stored
    assert len(storage.files) == 0
    # Verify monthly quota was preserved (still 5, not 6)
    refreshed_sub = session.get(Subscription, sub.id)
    assert refreshed_sub is not None
    assert refreshed_sub.reports_used_this_month == 5
