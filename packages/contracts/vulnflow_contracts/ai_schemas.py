"""AI Ghostwriter narrative contracts — SDD §2.6.1.3 (FR-AI / UC-11)."""

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AIJobStatus(StrEnum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class AINarrativeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tone: str = Field(default="formal_executive", pattern=r"^[a-zA-Z0-9_\- ]{1,30}$", max_length=30)
    language: str = Field(pattern=r"^(id|en)$")
    sections_requested: list[str] = Field(min_length=1)
    finding_ids: list[str] = Field(min_length=1)


class RemediationItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cwe_id: str
    vuln_title: str
    remediation_guidance: str


class NarrativeContent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    executive_summary: str
    business_impact: str
    remediations: list[RemediationItem] = Field(default_factory=list)


class AINarrativeResponse(BaseModel):
    """200 OK — SDD §2.6.1.3 contoh respons."""

    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    approval_status: Literal["DRAFT", "APPROVED"] = "DRAFT"
    narratives: NarrativeContent
    tokens_consumed: int = Field(ge=0)
    generated_at: datetime
    is_fallback: bool = Field(
        default=False, description="UC-11b / AD-02 — true saat Deterministic Fallback Engine aktif"
    )


class UpdateAINarrativeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    executive_summary: str = Field(min_length=1, max_length=20_000)
    business_impact: str = Field(min_length=1, max_length=20_000)
    remediations: list[RemediationItem] = Field(default_factory=list)
    approval_status: Literal["DRAFT", "APPROVED"] = "DRAFT"


class AINarrativeAcceptedResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: str
    status: AIJobStatus = AIJobStatus.QUEUED
    message: str
    status_url: str


class AINarrativeJobStatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: str
    status: AIJobStatus
    progress_percentage: int | None = Field(default=None, ge=0, le=100)
    stage: str | None = None
    narrative_id: str | None = None
    narrative: AINarrativeResponse | None = None
    error_message: str | None = None
