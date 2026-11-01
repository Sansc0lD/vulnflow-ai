"""Unit tests — FASE 4.3 contracts: workspace/project CRUD (SDD UC-04..UC-06a)."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from vulnflow_contracts import (
    APIKeyCreateRequest,
    APIKeyCreateResponse,
    AssignLeadRequest,
    InviteMemberRequest,
    InviteMemberResponse,
    ProjectCreateRequest,
    ProjectResponse,
    WorkspaceCreateRequest,
    WorkspaceResponse,
    WorkspaceRole,
    WorkspaceUpdateRequest,
)


def test_workspace_create_request_requires_non_empty_name() -> None:
    with pytest.raises(ValidationError):
        WorkspaceCreateRequest(name="")


def test_workspace_update_request_allows_partial_fields() -> None:
    update = WorkspaceUpdateRequest(brand_primary_color="#112233")
    assert update.name is None
    assert update.brand_primary_color == "#112233"


def test_workspace_update_request_rejects_invalid_hex_color() -> None:
    with pytest.raises(ValidationError):
        WorkspaceUpdateRequest(brand_primary_color="not-a-color")


def test_workspace_response_round_trip() -> None:
    response = WorkspaceResponse(
        id="ws-1",
        name="Agensi",
        brand_primary_color="#0F172A",
        brand_secondary_color="#3B82F6",
        created_at=datetime.now(UTC),
    )
    assert WorkspaceResponse.model_validate(response.model_dump(mode="json")) == response


def test_invite_member_request_round_trip() -> None:
    invite = InviteMemberRequest(email="new@example.com", role=WorkspaceRole.PENTESTER)
    assert invite.role == WorkspaceRole.PENTESTER


def test_invite_member_response_round_trip() -> None:
    response = InviteMemberResponse(invitation_token="t.o.k.e.n", expires_in=604800)
    assert response.expires_in == 604800


def test_api_key_create_request_requires_label() -> None:
    with pytest.raises(ValidationError):
        APIKeyCreateRequest(label="")


def test_api_key_create_response_round_trip() -> None:
    response = APIKeyCreateResponse(id="key-1", label="Laptop", api_key="vf_live_abc123")
    assert response.api_key == "vf_live_abc123"


def test_project_create_request_rejects_roe_end_before_start() -> None:
    with pytest.raises(ValidationError, match="roe_end_date must be after roe_start_date"):
        ProjectCreateRequest(
            name="Audit",
            client_name="Klien",
            target_scope=["*.klien.com"],
            roe_start_date=datetime(2026, 11, 1, tzinfo=UTC),
            roe_end_date=datetime(2026, 10, 1, tzinfo=UTC),
        )


def test_project_create_request_accepts_valid_roe_window() -> None:
    project = ProjectCreateRequest(
        name="Audit",
        client_name="Klien",
        target_scope=["*.klien.com", "10.20.0.0/24"],
        roe_start_date=datetime(2026, 10, 1, tzinfo=UTC),
        roe_end_date=datetime(2026, 11, 1, tzinfo=UTC),
    )
    assert project.timezone == "UTC"


def test_project_create_request_requires_at_least_one_scope_entry() -> None:
    with pytest.raises(ValidationError):
        ProjectCreateRequest(
            name="Audit",
            client_name="Klien",
            target_scope=[],
            roe_start_date=datetime(2026, 10, 1, tzinfo=UTC),
            roe_end_date=datetime(2026, 11, 1, tzinfo=UTC),
        )


def test_project_response_round_trip() -> None:
    response = ProjectResponse(
        id="prj-1",
        workspace_id="ws-1",
        name="Audit",
        client_name="Klien",
        target_scope=["*.klien.com"],
        roe_start_date=datetime(2026, 10, 1, tzinfo=UTC),
        roe_end_date=datetime(2026, 11, 1, tzinfo=UTC),
        timezone="Asia/Jakarta",
        status="ACTIVE",
    )
    assert ProjectResponse.model_validate(response.model_dump(mode="json")) == response


def test_assign_lead_request_round_trip() -> None:
    assert AssignLeadRequest(lead_pentester_id="user-1").lead_pentester_id == "user-1"


def test_project_create_request_rejects_naive_start_date() -> None:
    with pytest.raises(ValidationError, match="roe_start_date must be timezone-aware"):
        ProjectCreateRequest(
            name="Audit",
            client_name="Klien",
            target_scope=["*.klien.com"],
            roe_start_date=datetime(2026, 10, 1),
            roe_end_date=datetime(2026, 11, 1, tzinfo=UTC),
        )


def test_project_create_request_rejects_naive_end_date() -> None:
    with pytest.raises(ValidationError, match="roe_end_date must be timezone-aware"):
        ProjectCreateRequest(
            name="Audit",
            client_name="Klien",
            target_scope=["*.klien.com"],
            roe_start_date=datetime(2026, 10, 1, tzinfo=UTC),
            roe_end_date=datetime(2026, 11, 1),
        )


def test_project_create_request_rejects_invalid_timezone() -> None:
    with pytest.raises(ValidationError, match="Invalid IANA timezone"):
        ProjectCreateRequest(
            name="Audit",
            client_name="Klien",
            target_scope=["*.klien.com"],
            roe_start_date=datetime(2026, 10, 1, tzinfo=UTC),
            roe_end_date=datetime(2026, 11, 1, tzinfo=UTC),
            timezone="Mars/Olympus_Mons",
        )


def test_workspace_update_request_rejects_too_long_confidentiality_text() -> None:
    with pytest.raises(ValidationError):
        WorkspaceUpdateRequest(confidentiality_text="A" * 2001)
