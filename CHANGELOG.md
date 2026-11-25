# Changelog

All notable changes to **VulnFlow AI** are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-11-24

### Added
- **Monorepo Architecture (`uv` + `pnpm`)**: Structured workspace uniting `apps/api` (FastAPI + Celery), `apps/cli` (`vulnflow` CLI agent), `apps/web` (Vue 3 + TypeScript + Tailwind SPA), and `packages/contracts` (shared Pydantic V2 schemas).
- **Database & Security Layer (PostgreSQL 16 + Alembic `c3d4e5f6a703`)**:
  - 12 tables (`users`, `workspaces`, `workspace_members`, `subscriptions`, `api_keys`, `projects`, `findings`, `proofs_of_concept`, `ai_narratives`, `reports`, `enterprise_inquiries`, and monthly range-partitioned `audit_logs`).
  - AES-256-GCM at-rest encryption for raw Proof-of-Concept payloads (`apps/api/app/core/crypto.py`), Argon2id password hashing, stateless JWT revocation via `token_version`, and universal TOTP MFA.
- **Zero-PoC-to-AI & Stack-Aware Remediation Engine**:
  - `PromptSanitizationService` strictly whitelists abstract metadata (`title`, `cwe_id`, `cvss_score`, `severity`) and strips IPs, hostnames, ports, URLs, and exploit payloads before any external LLM request.
  - Asynchronous `ai_worker` Celery pipeline with SHA-256 Redis prompt caching, per-workspace rate limits, token/spend telemetry, Google Gemini adapter (`gemini-3-flash-preview` default with `gemini-2.5-flash-lite` fallback), private VPC `OllamaLLMAdapter`, and deterministic CWE catalog fallback (`DeterministicFallbackEngine`).
  - Optional project `tech_stack` context for stack-tailored remediation suggestions.
- **Local CLI Agent (`vulnflow`)**: `configure`, `setup-tools` (Nuclei binary provisioning), `scan`, and chunked idempotent `push` (`Idempotency-Key`, Nmap XML v1.04 & Nuclei JSONL streaming parsers, Free-tier 50-finding batch guard).
- **PDF Reporting, Branding & Tamper-Resistant Free-Tier Protection**:
  - Modular Jinja2 + WeasyPrint 70.0 PDF compilation with anti-SSRF `SafeURLFetcher` (pinned IP + SNI), PoC screenshot embedding, CVSS SVG radar, and WCAG 2.1 contrast checking.
  - Free-tier 180 DPI page rasterization (`pypdfium2` + `Pillow`), `pikepdf` permission lock, optional `pyHanko` PAdES DocMDP certification, PNG QR provenance (`segno`), and public `/verify/:code` verification.
- **Web SPA, Billing & Superadmin Portal**:
  - 6 public routes (`/`, `/about`, `/solutions`, `/solutions/:id`, `/contact`, `/verify/:code?`) and authenticated `/app/*` workspace dashboard + isolated `/app/admin` console (`AI Usage`, `Users`, `Workspaces & Plans`, `Audit Logs`).
  - Authenticated `/app/admin` console and `/app/settings` workspace switcher enforcing `MAX_FREE_WORKSPACES_PER_USER = 1` personal Free workspace limit per user.
  - Midtrans Snap PRO subscription checkout (`ORD-{hex}-{ts}-{rand}` within 50-char limit), fail-closed SHA-512 webhook verification, and sales-led Enterprise inquiry flow protected by Cloudflare Turnstile / signed Math-HMAC CAPTCHA (`captcha_service.py`).
- **Production Packaging & CI**:
  - Multi-stage Nginx SPA + Gunicorn overlay (`docker-compose.prod.yml`), GitHub Actions CI pipeline (`.github/workflows/ci.yml`), and full 18 Edge Case resilience suite (`EC-01`..`EC-18`).

### Fixed & Hardened
- Raised `BatchIngestRequest.findings` schema limit to `50,000` to align contract validation with workspace quota enforcement.
- Unified owner-password PDF permission locking with optional `pyHanko` PAdES DocMDP signing in `pdf_protector.py` so locked Free-tier PDFs sign without `PdfWriteError`.
- Enforced `User.status == "ACTIVE"` and active non-`VIEWER` workspace membership in CLI `X-API-Key` authentication, automatically revoking stale keys on account deletion, member removal, or `VIEWER` demotion.
- Protected `ENTERPRISE` subscriptions from conflicting Midtrans checkouts or webhook downgrades, cleared stale Midtrans tokens on admin tier overrides, and bounded CAPTCHA fallback challenge state with TTL cleanup and trusted-proxy IP checks.
- Eliminated Redis initial-state overwrite races (`nx=True` status initialization on async report/AI dispatches, lock contention retry in PDF compilation), restricted AI telemetry aggregation to the current UTC month, mapped curation/invite concurrency conflicts to HTTP `409`, and stored durable S3 `storage_path` keys with fresh presigned report download URLs.
- Fixed Web SPA async polling leaks, unmount/project-switch race conditions, logged-in `?invite=` redirect flow, and added Vue route-level lazy loading (eliminating the `> 500 kB` chunk warning).
- Hardened CLI API URL normalization, error handling for archive provisioning and Nmap XML parsing, dev/prod Docker volume isolation (`volumes: !reset []`), and Nginx `/assets/` security response headers.
- Widened `audit_logs.target_entity` from `VARCHAR(50)` to `VARCHAR(128)` via migration `c3d4e5f6a703` so entity identifiers such as `enterprise_inquiry:<uuid>` never trigger `StringDataRightTruncation` on PostgreSQL 16.
- Aligned `GeminiLLMAdapter` default model constant (`DEFAULT_GEMINI_MODEL`) to `gemini-3-flash-preview` to match `.env.example` and live AI Studio E2E verification.
- Wired package `__version__` (`1.0.0`) into `FastAPI(version=__version__)` so `/openapi.json` reports the live release version.
