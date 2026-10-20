"""PDF report compilation contracts — SDD §2.6.1.5 (FR-REP / UC-14, UC-14d)."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class ReportJobStatus(StrEnum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ThemeOptions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    primary_color: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")
    secondary_color: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")
    show_cover_page: bool = True
    show_cvss_radar: bool = True
    confidentiality_notice: str = ""


class CompilePDFRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    finding_ids: list[str] = Field(min_length=1)
    include_ai_narratives: bool = True
    theme_options: ThemeOptions | None = None


class CompilePDFAcceptedResponse(BaseModel):
    """202 Accepted — SDD §2.6.1.5 contoh respons."""

    model_config = ConfigDict(extra="forbid")

    job_id: str
    status: ReportJobStatus = ReportJobStatus.QUEUED
    message: str
    status_url: str


class ReportJobStatusResponse(BaseModel):
    """GET .../reports/jobs/{job_id} — bentuk field berbeda per status (SDD §2.6.1.5):
    QUEUED/PROCESSING -> progress_percentage; COMPLETED -> report_id/download_url;
    FAILED -> error_message. Field opsional dibiarkan None sesuai status aktif."""

    model_config = ConfigDict(extra="forbid")

    job_id: str
    status: ReportJobStatus
    progress_percentage: int | None = Field(default=None, ge=0, le=100)
    report_id: str | None = None
    download_url: str | None = None
    expires_in_seconds: int | None = Field(default=None, gt=0)
    error_message: str | None = None


class ReportDownloadResponse(BaseModel):
    """Bentuk JSON setara presigned URL segar — EC-17 (SDD §2.7.1), dipakai bila
    proxy download dikonsumsi sebagai API (bukan HTTP 307 redirect langsung)."""

    model_config = ConfigDict(extra="forbid")

    download_url: str
    expires_in_seconds: int = Field(gt=0)
