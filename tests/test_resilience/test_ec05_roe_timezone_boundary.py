"""PLAN.md FASE 7.2 — EC-05: Rules of Engagement (ROE) Timezone Boundary Differences.

SRS UC-06a & EDGE_CASES_AND_RESILIENCE.md §6 item 5:
Auditing projects operating in different regional timezones (e.g. client in Jakarta
UTC+7, auditor in London UTC+0) must never experience premature ROE expiration or
false out-of-boundary scans. The system strictly enforces timezone-aware TIMESTAMPTZ
datetime comparisons and valid IANA timezone identifiers.
"""

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import pytest
from pydantic import ValidationError

from vulnflow_contracts.workspace_schemas import ProjectCreateRequest


def test_ec05_rejects_naive_roe_datetimes() -> None:
    """Naive datetimes without tzinfo are strictly rejected to prevent timezone ambiguity."""
    with pytest.raises(ValidationError, match="timezone-aware"):
        ProjectCreateRequest(
            name="Audit Project",
            client_name="Client Corp",
            target_scope=["*.client.com"],
            roe_start_date=datetime(2026, 11, 1, 0, 0, 0),  # naive!
            roe_end_date=datetime(2026, 11, 10, 0, 0, 0, tzinfo=UTC),
            timezone="UTC",
        )


def test_ec05_rejects_invalid_iana_timezone() -> None:
    """Invalid timezone string fails validation."""
    with pytest.raises(ValidationError, match="Invalid IANA timezone"):
        ProjectCreateRequest(
            name="Audit Project",
            client_name="Client Corp",
            target_scope=["*.client.com"],
            roe_start_date=datetime(2026, 11, 1, 0, 0, 0, tzinfo=UTC),
            roe_end_date=datetime(2026, 11, 10, 0, 0, 0, tzinfo=UTC),
            timezone="NonExistent/Timezone_Invalid",
        )


def test_ec05_compares_cross_timezone_instants_accurately() -> None:
    """Start time in Jakarta (UTC+7) compared with UTC correctly preserves temporal order."""
    tz_jakarta = ZoneInfo("Asia/Jakarta")
    # Nov 1, 01:00 AM Jakarta time = Oct 31, 06:00 PM UTC
    start_jakarta = datetime(2026, 11, 1, 1, 0, 0, tzinfo=tz_jakarta)
    # Nov 1, 00:00 AM UTC = Nov 1, 07:00 AM Jakarta time
    end_utc = datetime(2026, 11, 1, 0, 0, 0, tzinfo=UTC)

    # start_jakarta is chronologically BEFORE end_utc (6 hours earlier in universal time)
    req = ProjectCreateRequest(
        name="Cross-Border Audit",
        client_name="Multi-Region Corp",
        target_scope=["*.corp.com"],
        roe_start_date=start_jakarta,
        roe_end_date=end_utc,
        timezone="Asia/Jakarta",
    )
    assert req.roe_start_date < req.roe_end_date

    # If end time in Jakarta is set to 00:30 AM (before start of 01:00 AM), must fail
    end_jakarta_before = datetime(2026, 11, 1, 0, 30, 0, tzinfo=tz_jakarta)
    with pytest.raises(ValidationError, match="roe_end_date must be after roe_start_date"):
        ProjectCreateRequest(
            name="Invalid Range",
            client_name="Client",
            target_scope=["*.corp.com"],
            roe_start_date=start_jakarta,
            roe_end_date=end_jakarta_before,
            timezone="Asia/Jakarta",
        )
