"""Midtrans webhook signature verification — PLAN.md FASE 4.8 (SDD §2.6.3.2)."""

import hashlib
import hmac


def verify_midtrans_signature(
    *, order_id: str, status_code: str, gross_amount: str, signature_key: str, server_key: str
) -> bool:
    # F4-HIGH-01: Fail-closed if server_key is empty or unset
    if not server_key or not server_key.strip():
        return False
    if not signature_key:
        return False

    expected = hashlib.sha512(
        f"{order_id}{status_code}{gross_amount}{server_key}".encode()
    ).hexdigest()
    # F4-LOW-13: encode ASCII bytes for safe constant-time comparison against non-ASCII inputs
    return hmac.compare_digest(
        expected.lower().encode("ascii"),
        signature_key.lower().encode("ascii", errors="ignore"),
    )
