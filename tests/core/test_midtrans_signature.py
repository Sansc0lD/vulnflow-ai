"""PLAN.md FASE 4.8 — Midtrans webhook signature verification (SDD §2.6.3.2)."""

import hashlib

from app.core.midtrans_signature import verify_midtrans_signature


def _valid_signature(order_id: str, status_code: str, gross_amount: str, server_key: str) -> str:
    raw = f"{order_id}{status_code}{gross_amount}{server_key}"
    return hashlib.sha512(raw.encode("utf-8")).hexdigest()


def test_verify_midtrans_signature_accepts_correct_signature() -> None:
    signature = _valid_signature("ORD-1", "200", "750000.00", "server-key-123")

    assert (
        verify_midtrans_signature(
            order_id="ORD-1",
            status_code="200",
            gross_amount="750000.00",
            signature_key=signature,
            server_key="server-key-123",
        )
        is True
    )


def test_verify_midtrans_signature_rejects_tampered_amount() -> None:
    signature = _valid_signature("ORD-1", "200", "750000.00", "server-key-123")

    assert (
        verify_midtrans_signature(
            order_id="ORD-1",
            status_code="200",
            gross_amount="1.00",  # tampered
            signature_key=signature,
            server_key="server-key-123",
        )
        is False
    )


def test_verify_midtrans_signature_is_case_insensitive() -> None:
    # SDD MED-05 audit note: signature comparison must be case-insensitive
    # hex comparison, not a byte-exact string match.
    signature = _valid_signature("ORD-1", "200", "750000.00", "server-key-123")

    assert (
        verify_midtrans_signature(
            order_id="ORD-1",
            status_code="200",
            gross_amount="750000.00",
            signature_key=signature.upper(),
            server_key="server-key-123",
        )
        is True
    )


def test_verify_midtrans_signature_rejects_wrong_server_key() -> None:
    signature = _valid_signature("ORD-1", "200", "750000.00", "server-key-123")

    assert (
        verify_midtrans_signature(
            order_id="ORD-1",
            status_code="200",
            gross_amount="750000.00",
            signature_key=signature,
            server_key="wrong-key",
        )
        is False
    )


def test_verify_midtrans_signature_fails_closed_when_server_key_empty() -> None:
    # F4-HIGH-01: fail-closed if server_key is empty/whitespace
    signature = _valid_signature("ORD-1", "200", "750000.00", "")
    assert not verify_midtrans_signature(
        order_id="ORD-1",
        status_code="200",
        gross_amount="750000.00",
        signature_key=signature,
        server_key="",
    )
    assert not verify_midtrans_signature(
        order_id="ORD-1",
        status_code="200",
        gross_amount="750000.00",
        signature_key=signature,
        server_key="   ",
    )


def test_verify_midtrans_signature_handles_non_ascii_safely() -> None:
    # F4-LOW-13: does not raise TypeError on non-ASCII input
    assert not verify_midtrans_signature(
        order_id="ORD-1",
        status_code="200",
        gross_amount="750000.00",
        signature_key="sig-with-non-ascii-🔥",
        server_key="server-key",
    )
