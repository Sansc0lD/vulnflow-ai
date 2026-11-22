"""Midtrans Snap billing contracts — SDD §2.6.3 (FR-SUB / UC-16)."""

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from vulnflow_contracts.auth_schemas import NormalizedEmail


class SubscriptionTier(StrEnum):
    """FR-SUB-001 — tier berbayar yang bisa di-checkout (FREE tidak dibeli)."""

    PRO = "PRO"
    ENTERPRISE = "ENTERPRISE"


class MidtransTransactionStatus(StrEnum):
    """SDD §2.6.3.2 alt-block: transaction_status yang ditangani handler webhook."""

    SETTLEMENT = "settlement"
    CAPTURE = "capture"
    PENDING = "pending"
    EXPIRE = "expire"
    CANCEL = "cancel"
    DENY = "deny"


class MidtransCheckoutRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tier: SubscriptionTier
    billing_cycle: str = "MONTHLY"


class MidtransCheckoutResponse(BaseModel):
    """200 OK — SDD §2.6.3.1 contoh respons."""

    model_config = ConfigDict(extra="forbid")

    order_id: str
    gross_amount: int = Field(gt=0)
    snap_token: str
    redirect_url: str


class MidtransWebhookPayload(BaseModel):
    """SDD §2.6.3.2 — `gross_amount` sengaja string 2-desimal (bukan number),
    sesuai "Catatan Normalisasi Signature Midtrans": nilai inilah yang masuk
    ke SHA-512(order_id + status_code + gross_amount + ServerKey). Validasi di
    sini hanya memeriksa FORMAT signature; verifikasi kriptografis sesungguhnya
    terhadap ServerKey adalah domain service di FASE 4 (BillingRouter).

    `extra="ignore"` (bukan "forbid") karena ini payload dari sistem eksternal
    (Midtrans) yang mengirim field tambahan standar (transaction_id,
    fraud_status, currency, dll.) di luar 7 field contoh SDD — field itu tidak
    kita perlukan, tapi menolaknya akan membuat webhook asli selalu gagal."""

    model_config = ConfigDict(extra="ignore")

    order_id: str
    status_code: str
    gross_amount: str = Field(pattern=r"^\d+\.\d{2}$")
    signature_key: str = Field(pattern=r"^[0-9a-fA-F]{128}$")
    transaction_status: MidtransTransactionStatus
    payment_type: str
    transaction_time: str
    fraud_status: str | None = None


class SubscriptionStatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workspace_id: str
    tier: str
    status: str
    monthly_report_quota: int = Field(ge=-1)
    is_unlimited: bool = False
    custom_batch_limit: int | None = None
    reports_used_this_month: int = Field(ge=0)
    remaining_reports: int = Field(ge=0)
    quota_reset_date: datetime
    payment_status: str
    payment_type: str | None = None
    midtrans_order_id: str | None = None


EnterpriseInquiryStatus = Literal["NEW", "CONTACTED", "PROVISIONED", "DECLINED"]


class EnterpriseInquiryCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_name: str = Field(min_length=1, max_length=150)
    contact_name: str = Field(min_length=1, max_length=150)
    contact_email: NormalizedEmail
    team_size: str = Field(default="5-20", min_length=1, max_length=50)
    estimated_monthly_reports: int | None = Field(default=None, ge=1, le=100_000)
    requirements: str = Field(min_length=5, max_length=4000)


class EnterpriseInquiryUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: EnterpriseInquiryStatus
    admin_notes: str | None = Field(default=None, max_length=2000)


class EnterpriseInquiryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    workspace_id: str | None = None
    submitted_by_user_id: str | None = None
    company_name: str
    contact_name: str
    contact_email: str
    team_size: str
    estimated_monthly_reports: int | None = None
    requirements: str
    status: EnterpriseInquiryStatus
    admin_notes: str | None = None
    created_at: datetime
    updated_at: datetime
