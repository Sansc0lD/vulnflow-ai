"""FastAPI application entrypoint — PLAN.md FASE 4.1.

Global exception handling, CORS, and security headers. Routers are
registered here as each one is implemented (FASE 4.2+).
"""

import os
from collections.abc import Awaitable, Callable, Mapping
from datetime import UTC, datetime

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppError
from app.routers import ai, auth, billing, ingest, projects, reports, triage, workspaces
from vulnflow_contracts import ErrorCode, StandardErrorEnvelope

app = FastAPI(title="VulnFlow AI API")
app.include_router(auth.router)
app.include_router(workspaces.router)
app.include_router(projects.router)
app.include_router(ingest.router)
app.include_router(triage.router)
app.include_router(ai.router)
app.include_router(reports.router)
app.include_router(reports.workspace_reports_router)
app.include_router(billing.router)
app.include_router(billing.webhook_router)

_SECURITY_HEADERS = {
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
}

_HTTP_STATUS_CODE_MAP = {
    400: ErrorCode.VALIDATION_FAILED,
    401: ErrorCode.AUTHENTICATION_FAILED,
    403: ErrorCode.PERMISSION_DENIED,
    404: ErrorCode.RESOURCE_NOT_FOUND,
    405: ErrorCode.RESOURCE_NOT_FOUND,
    409: ErrorCode.CONFLICT,
    413: ErrorCode.PAYLOAD_TOO_LARGE,
    422: ErrorCode.VALIDATION_FAILED,
}


def _get_cors_allowed_origins() -> list[str]:
    raw = os.environ.get("CORS_ALLOWED_ORIGINS", "http://localhost:5173")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_cors_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def _security_headers_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    response = await call_next(request)
    response.headers.update(_SECURITY_HEADERS)
    return response


def _error_response(
    status_code: int,
    code: ErrorCode,
    message: str,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    # F4-MED-09: Always include security headers on error envelopes, including 500
    envelope = StandardErrorEnvelope(code=code, message=message, timestamp=datetime.now(UTC))
    resp_headers = dict(_SECURITY_HEADERS)
    if headers:
        resp_headers.update(headers)
    return JSONResponse(
        status_code=status_code,
        content=envelope.model_dump(mode="json"),
        headers=resp_headers,
    )


@app.exception_handler(AppError)
async def _app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    return _error_response(exc.status_code, exc.error_code, str(exc))


@app.exception_handler(RequestValidationError)
async def _validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return _error_response(422, ErrorCode.VALIDATION_FAILED, "Request payload validation failed.")


@app.exception_handler(StarletteHTTPException)
async def _http_exception_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    # F4-MED-12: Standardize all HTTPExceptions (e.g. 404, 405, 400) into StandardErrorEnvelope
    code = _HTTP_STATUS_CODE_MAP.get(exc.status_code, ErrorCode.INTERNAL_SERVER_ERROR)
    message = str(exc.detail) if exc.detail else "HTTP error occurred."
    return _error_response(exc.status_code, code, message, headers=exc.headers)


@app.exception_handler(Exception)
async def _unhandled_exception_handler(_: Request, __: Exception) -> JSONResponse:
    # Never leak internal exception details (stack traces, DB errors) to
    # the client — SDD §2.5.1 Information Disclosure mitigation.
    return _error_response(
        500, ErrorCode.INTERNAL_SERVER_ERROR, "An internal server error occurred."
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
