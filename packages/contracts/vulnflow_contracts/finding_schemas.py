"""Finding ingestion contracts — SDD §2.6.1.1, §2.6.1.2, §2.6.1.6."""

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import AnyUrl, BaseModel, ConfigDict, Field


class Severity(StrEnum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class CVSSVersion(StrEnum):
    V3_1 = "3.1"
    V4_0 = "4.0"


class Protocol(StrEnum):
    TCP = "tcp"
    UDP = "udp"
    HTTP = "http"
    HTTPS = "https"
    ICMP = "icmp"
    SCTP = "sctp"
    OTHER = "other"


class SourceTool(StrEnum):
    NMAP = "nmap"
    NUCLEI = "nuclei"
    MANUAL = "manual"


class FindingStatus(StrEnum):
    """SRS UC-09 FR-TRG-001 — siklus hidup status kerentanan."""

    OPEN = "OPEN"
    IN_REVIEW = "IN_REVIEW"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    REMEDIATED = "REMEDIATED"
    ACCEPTED_RISK = "ACCEPTED_RISK"
    REOPENED = "REOPENED"


class ProofOfConceptSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    raw_evidence: str = Field(max_length=100_000)
    reproduction_steps: list[str] = Field(default_factory=list, max_length=100)
    attachment_urls: list[AnyUrl] = Field(default_factory=list, max_length=20)


class UnifiedVulnerabilityFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=255)
    severity: Severity
    cvss_version: CVSSVersion = CVSSVersion.V3_1
    cvss_score: float | None = Field(default=None, ge=0.0, le=10.0)
    cvss_vector: str | None = Field(
        default=None, pattern=r"^CVSS:3\.1/[A-Za-z0-9:\/._\-]+$", min_length=15, max_length=150
    )
    cwe_id: str = Field(default="UNKNOWN", pattern=r"^(CWE-[0-9]+|UNKNOWN)$")
    target_host: str = Field(max_length=255)
    target_port: int | None = Field(default=None, ge=0, le=65535)
    endpoint_path: str = Field(default="", max_length=500, description="EC-08 dedup_hash component")
    protocol: Protocol = Protocol.TCP
    source_tool: SourceTool
    proof_of_concept: ProofOfConceptSchema


class ScanMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scanner_name: str
    scanner_version: str
    scan_duration_seconds: float = Field(ge=0.0, allow_inf_nan=False)


class BatchIngestRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scan_metadata: ScanMetadata
    findings: list[UnifiedVulnerabilityFinding] = Field(min_length=1, max_length=500)


class BatchIngestResponse(BaseModel):
    """201 Created summary — UC-07 step 9: jumlah temuan baru vs terduplikasi."""

    model_config = ConfigDict(extra="forbid")

    new_findings_count: int = Field(ge=0)
    duplicate_findings_count: int = Field(ge=0)
    quarantined_count: int = Field(default=0, ge=0)


class ManualFindingRequest(BaseModel):
    """SDD §2.6.1.6 — entri manual tidak mengirim cvss_score/cvss_version;
    skor dihitung server-side dari cvss_vector (FASE 3 CVSSCalculator)."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=255)
    severity: Severity
    cvss_vector: str = Field(
        pattern=r"^CVSS:3\.1/[A-Za-z0-9:\/._\-]+$", min_length=15, max_length=150
    )
    cwe_id: str = Field(default="UNKNOWN", pattern=r"^(CWE-[0-9]+|UNKNOWN)$")
    target_host: str = Field(max_length=255)
    target_port: int | None = Field(default=None, ge=0, le=65535)
    endpoint_path: str = Field(default="", max_length=500, description="EC-08 dedup_hash component")
    protocol: Protocol = Protocol.TCP
    proof_of_concept: ProofOfConceptSchema


class ManualFindingResponse(BaseModel):
    """201 Created — SDD §2.6.1.6 contoh respons."""

    model_config = ConfigDict(extra="forbid")

    id: str
    project_id: str
    title: str
    severity: Severity
    cvss_score: float = Field(ge=0.0, le=10.0)
    cvss_vector: str
    cwe_id: str
    source_tool: Literal[SourceTool.MANUAL] = SourceTool.MANUAL
    status: FindingStatus
    created_at: datetime


class UpdateFindingStatusRequest(BaseModel):
    """PATCH .../findings/{f_id}/status — UC-09. `version` enables EC-11
    optimistic locking: a stale `version` is rejected with HTTP 409."""

    model_config = ConfigDict(extra="forbid")

    status: FindingStatus
    version: int = Field(ge=1)


class FindingStatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    status: FindingStatus
    version: int
    is_curated_for_report: bool
