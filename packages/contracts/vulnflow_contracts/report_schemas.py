"""PDF report compilation contracts — SDD §2.6.1.5 (FR-REP / UC-14, UC-14d)."""

from datetime import datetime
from enum import StrEnum
from typing import Literal

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
    show_toc: bool = True
    show_methodology: bool = True
    show_poc_attachments: bool = True
    report_language: Literal["en", "id"] = "en"
    methodology_framework: str = Field(default="OWASP WSTG & PTES", max_length=120)
    confidentiality_notice: str = Field(default="", max_length=2000)


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


class ReportSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    project_id: str
    report_title: str
    version: str
    watermark_applied: bool
    verification_code: str | None = None
    sha256_hash: str | None = None
    is_rasterized: bool = False
    is_signed: bool = False
    generated_at: datetime
    download_url: str


class PublicReportVerifyResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    valid: bool
    verification_code: str
    report_version: str | None = None
    agency_name: str | None = None
    generated_at: datetime | None = None
    watermark_applied: bool = False
    is_rasterized: bool = False
    is_signed: bool = False
    sha256_hash: str | None = None
