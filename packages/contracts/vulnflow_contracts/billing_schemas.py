"""Midtrans Snap billing contracts — SDD §2.6.3 (FR-SUB / UC-16)."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


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
