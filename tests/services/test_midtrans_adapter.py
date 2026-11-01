"""PLAN.md FASE 4.8 — MidtransAdapter (Snap transaction creation)."""

import httpx
import pytest
from app.services.midtrans_adapter import MidtransAdapter, MidtransCheckoutError


def test_create_transaction_returns_snap_token_and_redirect_url() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            201,
            json={
                "token": "snap-token-abc",
                "redirect_url": "https://app.sandbox.midtrans.com/snap/v3/redirection/abc",
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    adapter = MidtransAdapter(server_key="server-key", client=client, is_production=False)

    snap_token, redirect_url = adapter.create_transaction(order_id="ORD-1", gross_amount=750000)

    assert snap_token == "snap-token-abc"
    assert redirect_url == "https://app.sandbox.midtrans.com/snap/v3/redirection/abc"


def test_create_transaction_sends_order_id_and_amount_in_payload() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        import json

        captured["body"] = json.loads(request.content)
        return httpx.Response(201, json={"token": "t", "redirect_url": "https://x"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    adapter = MidtransAdapter(server_key="server-key", client=client, is_production=False)

    adapter.create_transaction(order_id="ORD-42", gross_amount=750000)

    body = captured["body"]
    assert body["transaction_details"]["order_id"] == "ORD-42"
    assert body["transaction_details"]["gross_amount"] == 750000


def test_create_transaction_raises_checkout_error_on_failure() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, text="Internal gateway database error sensitive details")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    adapter = MidtransAdapter(server_key="server-key", client=client, is_production=False)

    with pytest.raises(MidtransCheckoutError) as exc_info:
        adapter.create_transaction(order_id="ORD-1", gross_amount=750000)

    # F4-MED-04: Do not leak raw sensitive gateway text in exception message
    assert "Internal gateway database error" not in str(exc_info.value)


def test_create_transaction_handles_malformed_json_response() -> None:
    # F4-LOW-01: Malformed JSON upstream should raise MidtransCheckoutError
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<html>502 Bad Gateway</html>")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    adapter = MidtransAdapter(server_key="server-key", client=client, is_production=False)

    with pytest.raises(MidtransCheckoutError, match="missing or malformed"):
        adapter.create_transaction(order_id="ORD-1", gross_amount=750000)
