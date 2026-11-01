"""PLAN.md FASE 4.1 — global exception handling, CORS, security headers."""

from app.core.exceptions import AuthenticationError
from app.main import app
from fastapi.testclient import TestClient


def test_health_endpoint_returns_ok() -> None:
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_app_error_is_wrapped_in_standard_error_envelope() -> None:
    @app.get("/__test/auth-error")
    def _raise_auth_error() -> None:
        raise AuthenticationError("bad token")

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/__test/auth-error")

    assert response.status_code == 401
    body = response.json()
    assert body["status"] == "error"
    assert body["code"] == "AUTHENTICATION_FAILED"
    assert body["message"] == "bad token"
    assert "timestamp" in body


def test_unhandled_exception_is_wrapped_as_internal_server_error() -> None:
    @app.get("/__test/boom")
    def _raise_unexpected() -> None:
        raise RuntimeError("boom")

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/__test/boom")

    assert response.status_code == 500
    body = response.json()
    assert body["code"] == "INTERNAL_SERVER_ERROR"
    # Internal exception details must never leak to the client.
    assert "boom" not in body["message"]


def test_request_validation_error_is_wrapped_as_validation_failed() -> None:
    @app.get("/__test/needs-int")
    def _needs_int(value: int) -> dict[str, int]:
        return {"value": value}

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/__test/needs-int", params={"value": "not-an-int"})

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_FAILED"


def test_security_headers_present_on_every_response() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert "max-age=" in response.headers["strict-transport-security"]
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert "content-security-policy" in response.headers


def test_cors_allows_configured_origin(monkeypatch: object) -> None:
    with TestClient(app) as client:
        response = client.get("/health", headers={"Origin": "http://localhost:5173"})

    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_404_not_found_returns_standard_error_envelope_with_security_headers() -> None:
    # F4-MED-09 & F4-MED-12: Non-existent routes return StandardErrorEnvelope + security headers
    with TestClient(app) as client:
        response = client.get("/non-existent-endpoint-xyz")

    assert response.status_code == 404
    body = response.json()
    assert body["status"] == "error"
    assert body["code"] == "RESOURCE_NOT_FOUND"
    assert "timestamp" in body

    # Security headers on error response
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert "max-age=" in response.headers["strict-transport-security"]


def test_405_method_not_allowed_returns_standard_error_envelope() -> None:
    # F4-MED-12: 405 Method Not Allowed mapped to StandardErrorEnvelope
    with TestClient(app) as client:
        response = client.post("/health")

    assert response.status_code == 405
    body = response.json()
    assert body["status"] == "error"
    assert body["code"] == "RESOURCE_NOT_FOUND"


def test_500_internal_error_includes_security_headers() -> None:
    # F4-MED-09: 500 responses retain security headers
    @app.get("/__test/server-crash")
    def _crash() -> None:
        raise RuntimeError("simulated server crash")

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/__test/server-crash")

    assert response.status_code == 500
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert "max-age=" in response.headers["strict-transport-security"]
