"""Standard error envelope — SDD §2.6.1.7 (RFC 9110)."""

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict


class ErrorCode(StrEnum):
    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    QUOTA_EXHAUSTED = "QUOTA_EXHAUSTED"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    BATCH_LIMIT_EXCEEDED = "BATCH_LIMIT_EXCEEDED"
    PAYLOAD_TOO_LARGE = "PAYLOAD_TOO_LARGE"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"


class ErrorDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field: str
    issue: str


class StandardErrorEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["error"] = "error"
    code: ErrorCode
    message: str
    details: ErrorDetail | None = None
    timestamp: datetime
