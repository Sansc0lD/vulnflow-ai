"""MidtransAdapter — SDD UC-16 `MidtransClient` (Snap transaction API)."""

import base64

import httpx

_SANDBOX_URL = "https://app.sandbox.midtrans.com/snap/v1/transactions"
_PRODUCTION_URL = "https://app.midtrans.com/snap/v1/transactions"


class MidtransCheckoutError(Exception):
    pass


class MidtransAdapter:
    def __init__(self, *, server_key: str, client: httpx.Client, is_production: bool) -> None:
        self._server_key = server_key
        self._client = client
        self._url = _PRODUCTION_URL if is_production else _SANDBOX_URL

    def create_transaction(self, *, order_id: str, gross_amount: int) -> tuple[str, str]:
        auth = base64.b64encode(f"{self._server_key}:".encode()).decode()
        try:
            response = self._client.post(
                self._url,
                headers={"Authorization": f"Basic {auth}"},
                json={"transaction_details": {"order_id": order_id, "gross_amount": gross_amount}},
            )
        except httpx.TransportError as exc:
            raise MidtransCheckoutError("Could not reach Midtrans.") from exc

        if response.status_code >= 400:
            # F4-MED-04: Do not leak raw gateway response text to clients
            raise MidtransCheckoutError(
                f"Midtrans checkout failed with status {response.status_code}."
            )

        try:
            # F4-LOW-01: catch JSON decode or type errors
            data = response.json()
            return data["token"], data["redirect_url"]
        except (KeyError, TypeError, ValueError) as exc:
            raise MidtransCheckoutError(
                "Midtrans response missing or malformed token/redirect_url."
            ) from exc
