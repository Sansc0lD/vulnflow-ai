"""Workspace & project CRUD contracts — SDD UC-04..UC-06a (added FASE 4.3)."""

from datetime import datetime
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator

from vulnflow_contracts.auth_schemas import NormalizedEmail, WorkspaceRole


class WorkspaceCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=150)


class WorkspaceUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=150)
    custom_logo_url: str | None = Field(default=None, max_length=500)
    brand_primary_color: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    brand_secondary_color: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    confidentiality_text: str | None = Field(default=None, max_length=2000)


class WorkspaceResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    custom_logo_url: str | None = None
    brand_primary_color: str
    brand_secondary_color: str
    created_at: datetime


class InviteMemberRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: NormalizedEmail
    role: WorkspaceRole


class InviteMemberResponse(BaseModel):
    """EC-02 — signed invitation token, 7-day TTL."""

    model_config = ConfigDict(extra="forbid")

    invitation_token: str
    expires_in: int = Field(gt=0)


class APIKeyCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str = Field(min_length=1, max_length=100)


class APIKeyCreateResponse(BaseModel):
    """Raw key is only ever shown once — only `key_hash` is persisted."""

    model_config = ConfigDict(extra="forbid")

    id: str
    label: str
    api_key: str


class ProjectCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=150)
    client_name: str = Field(min_length=1, max_length=150)
    target_scope: list[str] = Field(min_length=1)
    roe_start_date: datetime
    roe_end_date: datetime
    timezone: str = Field(default="UTC", max_length=50)

    @field_validator("timezone")
    @classmethod
    def _validate_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except Exception:
            raise ValueError(f"Invalid IANA timezone: {value}") from None
        return value

    @field_validator("roe_start_date")
    @classmethod
    def _roe_start_must_be_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            raise ValueError("roe_start_date must be timezone-aware")
        return value

    @field_validator("roe_end_date")
    @classmethod
    def _roe_end_after_start(cls, value: datetime, info: ValidationInfo) -> datetime:
        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            raise ValueError("roe_end_date must be timezone-aware")
        start = info.data.get("roe_start_date")
        if start is not None:
            try:
                if value <= start:
                    raise ValueError("roe_end_date must be after roe_start_date")
            except TypeError as exc:
                raise ValueError(
                    "roe_end_date and roe_start_date must both be timezone-aware"
                ) from exc
        return value


class ProjectResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    workspace_id: str
    name: str
    client_name: str
    target_scope: list[str]
    roe_start_date: datetime
    roe_end_date: datetime
    timezone: str
    status: str
    lead_pentester_id: str | None = None


class AssignLeadRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lead_pentester_id: str
