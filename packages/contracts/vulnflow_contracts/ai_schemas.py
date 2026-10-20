"""AI Ghostwriter narrative contracts — SDD §2.6.1.3 (FR-AI / UC-11)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AINarrativeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tone: str = "formal_executive"
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

    narratives: NarrativeContent
    tokens_consumed: int = Field(ge=0)
    generated_at: datetime
    is_fallback: bool = Field(
        default=False, description="UC-11b / AD-02 — true saat Deterministic Fallback Engine aktif"
    )
