"""PLAN.md FASE 4.7 — compile_report orchestration (EC-16 quota rollback on crash)."""

import uuid
from collections.abc import Generator
from datetime import UTC, datetime, timedelta

import pytest
from app.core.exceptions import QuotaExhaustedError, ResourceNotFoundError
from app.models.base import Base
from app.models.finding import Finding
from app.models.project import Project
from app.models.report import Report
from app.models.subscription import Subscription
from app.models.workspace import Workspace
from app.workers.report_worker import compile_report
from sqlalchemy import create_engine
from sqlalchemy.orm import Session


class _FakeS3:
    def __init__(self) -> None:
        self.uploaded: dict[str, bytes] = {}
        self.deleted: list[str] = []

    def upload_bytes(self, key: str, data: bytes) -> None:
        self.uploaded[key] = data

    def delete_file(self, key: str) -> None:
        self.uploaded.pop(key, None)
        self.deleted.append(key)


def _renderer_ok(html: str) -> bytes:
    return b"%PDF-fake"


def _renderer_crashes(html: str) -> bytes:
    raise RuntimeError("WeasyPrint OOM / PDF bomb")


@pytest.fixture
def session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


def _make_project_with_finding(session: Session, *, quota: int, used: int) -> Project:
    workspace = Workspace(name="Agensi")
    session.add(workspace)
    session.commit()
    session.add(
        Subscription(
            workspace_id=workspace.id,
            tier="FREE",
            monthly_report_quota=quota,
            reports_used_this_month=used,
            quota_reset_date=datetime.now(UTC) + timedelta(days=30),
        )
    )
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
    from decimal import Decimal

    session.add(
        Finding(
            project_id=project.id,
            dedup_hash="h",
            title="First finding Alpha",
            severity="LOW",
            cvss_score=Decimal("1.0"),
            cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:N",
            cwe_id="UNKNOWN",
            target_host="app.klien.com",
            source_tool="manual",
        )
    )
    session.commit()
    return project


def test_compile_report_uploads_pdf_and_persists_report_row(session: Session) -> None:
    project = _make_project_with_finding(session, quota=3, used=0)
    s3 = _FakeS3()

    report = compile_report(
        session,
        s3,
        workspace_id=project.workspace_id,
        project_id=project.id,
        report_title="Laporan",
        executive_summary="Ringkasan.",
        business_impact="Dampak.",
        render_fn=_renderer_ok,
        watermark_text=None,
    )

    assert isinstance(report, Report)
    assert s3.uploaded[report.storage_path] == b"%PDF-fake"

    subscription = session.query(Subscription).filter_by(workspace_id=project.workspace_id).one()
    assert subscription.reports_used_this_month == 1


def test_compile_report_rejects_when_quota_exhausted(session: Session) -> None:
    project = _make_project_with_finding(session, quota=3, used=3)
    s3 = _FakeS3()

    with pytest.raises(QuotaExhaustedError):
        compile_report(
            session,
            s3,
            workspace_id=project.workspace_id,
            project_id=project.id,
            report_title="Laporan",
            executive_summary="",
            business_impact="",
            render_fn=_renderer_ok,
            watermark_text=None,
        )

    subscription = session.query(Subscription).filter_by(workspace_id=project.workspace_id).one()
    assert subscription.reports_used_this_month == 3  # unchanged


def test_compile_report_rolls_back_quota_on_render_crash(session: Session) -> None:
    # EC-16: a WeasyPrint crash (e.g. PDF bomb / OOM) must not consume quota
    # or leave a half-written Report row behind.
    project = _make_project_with_finding(session, quota=3, used=0)
    s3 = _FakeS3()

    with pytest.raises(RuntimeError, match="PDF bomb"):
        compile_report(
            session,
            s3,
            workspace_id=project.workspace_id,
            project_id=project.id,
            report_title="Laporan",
            executive_summary="",
            business_impact="",
            render_fn=_renderer_crashes,
            watermark_text=None,
        )

    subscription = session.query(Subscription).filter_by(workspace_id=project.workspace_id).one()
    assert subscription.reports_used_this_month == 0  # not incremented
    assert session.query(Report).count() == 0  # no partial row persisted
    assert s3.uploaded == {}  # nothing uploaded


def test_compile_report_applies_free_tier_watermark(session: Session) -> None:
    project = _make_project_with_finding(session, quota=3, used=0)
    s3 = _FakeS3()

    report = compile_report(
        session,
        s3,
        workspace_id=project.workspace_id,
        project_id=project.id,
        report_title="Laporan",
        executive_summary="",
        business_impact="",
        render_fn=_renderer_ok,
        watermark_text="FREE TIER",
    )

    assert report.watermark_applied is True


def test_compile_report_fails_closed_when_subscription_missing(session: Session) -> None:
    # F4-LOW-02, F4-HIGH-09
    workspace = Workspace(name="NoSub")
    session.add(workspace)
    session.commit()
    project = Project(
        workspace_id=workspace.id,
        name="P",
        client_name="C",
        target_scope="*.c.com",
        roe_start_date=datetime(2026, 10, 1, tzinfo=UTC),
        roe_end_date=datetime(2026, 11, 1, tzinfo=UTC),
    )
    session.add(project)
    session.commit()

    s3 = _FakeS3()
    with pytest.raises(QuotaExhaustedError, match="No active subscription found"):
        compile_report(
            session,
            s3,
            workspace_id=workspace.id,
            project_id=project.id,
            report_title="T",
            executive_summary="",
            business_impact="",
            render_fn=_renderer_ok,
            watermark_text=None,
        )


def test_compile_report_resets_quota_when_quota_reset_date_passed(session: Session) -> None:
    # F4-HIGH-10
    project = _make_project_with_finding(session, quota=3, used=3)
    subscription = session.query(Subscription).filter_by(workspace_id=project.workspace_id).one()
    past_date = datetime.now(UTC) - timedelta(days=2)
    subscription.quota_reset_date = past_date
    session.commit()

    s3 = _FakeS3()
    report = compile_report(
        session,
        s3,
        workspace_id=project.workspace_id,
        project_id=project.id,
        report_title="Laporan",
        executive_summary="",
        business_impact="",
        render_fn=_renderer_ok,
        watermark_text=None,
    )
    assert isinstance(report, Report)
    subscription = session.query(Subscription).filter_by(workspace_id=project.workspace_id).one()
    assert subscription.reports_used_this_month == 1
    reset_dt = (
        subscription.quota_reset_date
        if subscription.quota_reset_date.tzinfo is not None
        else subscription.quota_reset_date.replace(tzinfo=UTC)
    )
    assert reset_dt > datetime.now(UTC)


def test_compile_report_rejects_cross_tenant_or_missing_project(session: Session) -> None:
    # F4-LOW-03
    project = _make_project_with_finding(session, quota=3, used=0)
    other_workspace_id = uuid.uuid4()
    session.add(
        Subscription(
            workspace_id=other_workspace_id,
            tier="FREE",
            monthly_report_quota=3,
            reports_used_this_month=0,
            quota_reset_date=datetime.now(UTC) + timedelta(days=30),
        )
    )
    session.commit()
    s3 = _FakeS3()

    with pytest.raises(ResourceNotFoundError):
        compile_report(
            session,
            s3,
            workspace_id=other_workspace_id,
            project_id=project.id,
            report_title="T",
            executive_summary="",
            business_impact="",
            render_fn=_renderer_ok,
            watermark_text=None,
        )


def test_compile_report_filters_by_finding_ids(session: Session) -> None:
    # F4-MED-13
    project = _make_project_with_finding(session, quota=3, used=0)
    from decimal import Decimal

    f2 = Finding(
        project_id=project.id,
        dedup_hash="h2",
        title="Second finding Beta",
        severity="HIGH",
        cvss_score=Decimal("8.0"),
        cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N",
        cwe_id="CWE-79",
        target_host="app.klien.com",
        source_tool="manual",
    )
    session.add(f2)
    session.commit()

    s3 = _FakeS3()
    captured_html = []

    def capturing_render(html: str) -> bytes:
        captured_html.append(html)
        return b"%PDF-fake"

    compile_report(
        session,
        s3,
        workspace_id=project.workspace_id,
        project_id=project.id,
        report_title="Laporan Filtered",
        executive_summary="",
        business_impact="",
        finding_ids=[str(f2.id)],
        render_fn=capturing_render,
        watermark_text=None,
    )
    assert len(captured_html) == 1
    assert "Second finding Beta" in captured_html[0]
    assert "First finding Alpha" not in captured_html[0]


def test_compile_report_cleans_up_s3_when_commit_fails(
    session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    # F4-LOW-04
    project = _make_project_with_finding(session, quota=3, used=0)
    s3 = _FakeS3()

    def boom() -> None:
        raise RuntimeError("DB commit failed")

    monkeypatch.setattr(session, "commit", boom)

    with pytest.raises(RuntimeError, match="DB commit failed"):
        compile_report(
            session,
            s3,
            workspace_id=project.workspace_id,
            project_id=project.id,
            report_title="T",
            executive_summary="",
            business_impact="",
            render_fn=_renderer_ok,
            watermark_text=None,
        )

    assert len(s3.deleted) == 1
