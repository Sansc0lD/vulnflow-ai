"""Superadmin telemetry, user governance, and audit contracts (FR-ADM / UC-17..19)."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class WorkspaceTokenUsage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workspace_id: str
    workspace_name: str
    total_tokens: int = Field(ge=0)
    narrative_count: int = Field(ge=0)
    fallback_count: int = Field(ge=0)
    estimated_cost_usd: float = Field(ge=0.0)
    estimated_cost_idr: int = Field(ge=0)


class AITelemetryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_tokens: int = Field(ge=0)
    total_narratives: int = Field(ge=0)
    fallback_count: int = Field(ge=0)
    fallback_ratio: float = Field(ge=0.0, le=1.0)
    estimated_cost_usd: float = Field(ge=0.0)
    estimated_cost_idr: int = Field(ge=0)
    monthly_spend_ceiling_usd: float = Field(gt=0.0)
    circuit_breaker_active: bool
    by_workspace: list[WorkspaceTokenUsage] = Field(default_factory=list)


class AdminUserSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    email: str
    full_name: str
    status: str
    is_superadmin: bool
    mfa_enabled: bool
    created_at: datetime
    workspace_count: int = Field(ge=0)


class SuspendUserRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str = Field(min_length=3, max_length=500)


class SpendCeilingUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    monthly_spend_ceiling_usd: float = Field(gt=0.0, le=100_000.0)


class AdminWorkspaceSubscriptionSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workspace_id: str
    workspace_name: str
    tier: str
    status: str
    monthly_report_quota: int = Field(ge=-1)
    is_unlimited: bool = False
    reports_used_this_month: int = Field(ge=0)
    custom_batch_limit: int | None = None
    quota_reset_date: datetime
    payment_status: str
    manager_emails: list[str] = Field(default_factory=list)
    created_at: datetime


class AdminSubscriptionOverrideRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tier: Literal["FREE", "PRO", "ENTERPRISE"]
    monthly_report_quota: int = Field(ge=-1, le=100_000)
    custom_batch_limit: int | None = Field(default=None, ge=50, le=50_000)
    reason: str = Field(min_length=3, max_length=500)
