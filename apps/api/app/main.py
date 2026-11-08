"""FastAPI application entrypoint — PLAN.md FASE 4.1.

Global exception handling, CORS, and security headers. Routers are
registered here as each one is implemented (FASE 4.2+).
"""

import os
import secrets
from collections.abc import Awaitable, Callable, Mapping
from datetime import UTC, datetime

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppError
from app.routers import ai, auth, billing, ingest, projects, reports, triage, workspaces
from vulnflow_contracts import ErrorCode, StandardErrorEnvelope

# Default docs/redoc are disabled here and re-registered below as custom
# routes: Swagger UI's generated page includes one inline <script> block
# that initializes SwaggerUIBundle, which SDD §2.6.1.8's "strict nonce-based
# CSP" requirement is specifically meant to allow without weakening
# script-src to 'unsafe-inline' (confirmed live via headless Chromium: under
# the old scoped-but-nonce-less policy, that inline script was silently
# blocked and the page rendered completely blank — `curl` can't catch this
# since it doesn't execute JS or enforce CSP).
app = FastAPI(title="VulnFlow AI API", docs_url=None, redoc_url=None)
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


# Swagger UI / ReDoc load their JS/CSS bundles from jsdelivr's CDN, which the
# default `default-src 'none'` policy above blocks outright. An earlier pass
# "fixed" this by deleting the CSP header entirely on these paths, leaving
# them with zero CSP protection on an unauthenticated, always-on route — this
# scopes the policy down to exactly what those two renderers need instead.
# `https://cdn.redoc.ly` is ReDoc's own small logo image; Google Fonts is
# deliberately NOT allowlisted here — `with_google_fonts=False` below drops
# that cosmetic-only dependency instead of widening style-src/font-src for it.
def _docs_content_security_policy(nonce: str) -> str:
    return (
        "default-src 'none'; "
        f"script-src 'self' 'nonce-{nonce}' https://cdn.jsdelivr.net; "
        "style-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
        "img-src 'self' data: https://fastapi.tiangolo.com https://cdn.redoc.ly; "
        "font-src 'self' data:; "
        "connect-src 'self'; "
        "worker-src blob:;"
    )


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
    is_docs_path = request.url.path.startswith(("/docs", "/redoc", "/openapi"))
    if is_docs_path:
        # Generated once per request and read back below after `call_next`
        # returns — the custom /docs route reads this same value off
        # `request.state` to stamp the one inline <script> it emits, so the
        # CSP header and the script tag always agree on the same nonce.
        request.state.csp_nonce = secrets.token_urlsafe(16)

    response = await call_next(request)
    response.headers.update(_SECURITY_HEADERS)
    if is_docs_path:
        response.headers["Content-Security-Policy"] = _docs_content_security_policy(
            request.state.csp_nonce
        )
    return response


@app.get("/docs", include_in_schema=False)
async def _swagger_ui_html(request: Request) -> HTMLResponse:
    response = get_swagger_ui_html(
        openapi_url=app.openapi_url or "/openapi.json",
        title=f"{app.title} - Swagger UI",
    )
    html = bytes(response.body).decode("utf-8")
    # The only inline (no `src`) <script> tag in FastAPI's generated page is
    # the SwaggerUIBundle initializer — stamp it with this request's nonce
    # so the CSP above can allow exactly that script without 'unsafe-inline'
    # or a content hash that would silently break on any FastAPI upgrade
    # that changes this generated markup even by whitespace.
    html = html.replace("<script>\n", f'<script nonce="{request.state.csp_nonce}">\n', 1)
    return HTMLResponse(html)


@app.get("/redoc", include_in_schema=False)
async def _redoc_html() -> HTMLResponse:
    # ReDoc's generated page has no inline <script> — it self-initializes
    # from the `<redoc spec-url=...>` element once its external bundle
    # loads — so no nonce is needed here.
    return get_redoc_html(
        openapi_url=app.openapi_url or "/openapi.json",
        title=f"{app.title} - ReDoc",
        with_google_fonts=False,
    )


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
