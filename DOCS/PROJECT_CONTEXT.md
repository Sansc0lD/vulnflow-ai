# VulnFlow AI — Full Project Context

> Snapshot date: 2026-11-20. FASE 0–7 & Live Full-Stack E2E verification complete (monorepo scaffolding, contracts, DB layer + live PostgreSQL 16 semantics, domain engines, routers + Celery worker, CLI agent, Vue 3 + TypeScript SPA frontend, 18/18 EC resilience tests, and end-to-end 6-container Docker/WeasyPrint/MinIO/Mailpit/Gemini/Midtrans/Browser verification).
> This is a derived summary for onboarding/orientation. On any conflict, the authoritative sources are `SRS.md`, `SDD.md`, `EDGE_CASES_AND_RESILIENCE.md`, and `PLAN.md` in this same directory — re-check them, as this file can go stale.

## 1. Product Purpose & Key Constraints

**VulnFlow AI** is a SaaS vulnerability-management and AI-assisted reporting platform for pentesters/bug hunters/agencies, built as the **IPPL** (*Implementasi Perancangan Perangkat Lunak*) university capstone using Spec-Driven Development + TDD. It solves three problems:

1. 35–50% of pentester time wasted on manual reporting.
2. Fragmented scanner output formats (Nmap XML vs. Nuclei JSON).
3. Risk of leaking sensitive client infrastructure data to commercial AI providers (and triggering AI safety-filter refusals).

### The core architectural guarantee — "Zero-PoC to AI"

(SRS §1.4, §2.4; SDD §1.3, §2.5.3)

> *"Aturan 'Zero-PoC to AI': Modul backend SaaS dilarang keras meneruskan teks raw request/response, muatan serangan (payload string), alamat IP/hostname target, atau kredensial hasil pemindaian ke API LLM eksternal. Pelanggaran terhadap batasan ini dieliminasi melalui modul Data Sanitizer Layer otomatis."*

- Enforced by a planned **`SanitizerService`** / **`PromptSanitizationService`** (`apps/api/app/domain/sanitizer.py`, FASE 3.4) sitting between `AIGhostwriterService` and `LLMAdapter`. Per SDD §2.5.3: strict column whitelisting (only `title`, `cwe_id`, `cvss_score`, `severity` pass through), PoC/PII stripping (IPs, ports, intranet domains, raw payloads removed), and adversarial prompt-injection character escaping.
- Already encoded structurally in the Pydantic contracts: `UnifiedVulnerabilityFinding`/`ProofOfConceptSchema` (raw target/PoC data, DB-only) vs. `AINarrativeRequest`/`NarrativeContent` (abstract `finding_ids` + taxonomy only, never raw PoC).
- Dual purpose: client confidentiality **and** avoiding commercial LLM safety-filter refusals triggered by concrete exploit strings (e.g. `' UNION SELECT...`).
- Related constraints: the SaaS server never scans targets directly (all active scanning happens on the pentester's local machine via the CLI agent); v1.0 scanner support limited to Nmap XML v1.04 and Nuclei JSON v3.

## 2. Architecture Overview (C4 Model, SDD §2.2)

**Deployment topology**: Hybrid distributed — local CLI Agent on the pentester's machine (Kali/Parrot/macOS/Windows+WSL2) talks over HTTPS to a cloud SaaS backend; the SaaS server never scans targets itself.

**C4 L1 (Context)**: Actors — Pentester, Agency Manager, Superadmin. External systems — Target Infrastructure (scanned only locally by the pentester), LLM Provider (Vertex AI/OpenAI), Cloud Object Storage (S3/MinIO), Midtrans Payment Gateway.

**C4 L2 (Containers)**:
- Client: Local CLI Agent (Python 3.12+, Typer/Rich/HTTPX/Pydantic), Scanner binaries (Nmap 7.9+, Nuclei v3+), Browser running Vue 3 + Tailwind + Vite SPA.
- Cloud: Nginx/Cloudflare reverse proxy (TLS 1.3, rate limiting) → FastAPI Backend Core API (auth, business logic, sanitizer, billing) → PostgreSQL 16 (11 tables, AES-256-GCM, declarative partitioning), Redis 7.2 (Celery broker, token blacklist, metrics), MinIO/S3 (logos & PDF artifacts); a separate WeasyPrint-based Report/PDF async worker consumes Redis-queued jobs.
- External: LLM Provider API (abstract metadata only), Midtrans Snap/Webhooks (SHA-512 signed).

**C4 L3 (Backend Components, layered/hexagonal)**:
- Presentation: `AuthCtrl`, `IngestCtrl`, `ProjectCtrl`, `TriageCtrl`, `ReportCtrl`, `BillingCtrl`, `AdminCtrl`.
- Domain services: `RBACService`, `ScopeValidator`, `DeduplicationEngine`, `SanitizerService`, `AIGhostwriterService`, `CWEFallbackService`, `ReportCompilerService`, `QuotaGuardService`.
- Persistence/adapters: `DBRepo` (SQLAlchemy 2.0), `RedisAdapter`, `S3StorageAdapter`, `LLMAdapter`, `MidtransAdapter`.

**C4 L4 (Design patterns)**: Strategy pattern for scanner parsers (`BaseScannerParser` → `NmapXmlParser`, `NucleiJsonParser`); Factory/Adapter pattern for LLM providers (`LLMProviderFactory` → `ILLMAdapter` for Gemini/OpenAI/Ollama); Repository pattern for persistence.

**Activity diagrams** map to use cases:
- **AD-01**: ingestion pipeline (local scan → CLI parse/hash → API auth/scope/quota checks → dedup → atomic DB commit + PoC encryption).
- **AD-02**: AI sanitization/ghostwriting/fallback pipeline (sanitize → abstract metadata → LLM call → schema validation → fallback-on-failure → human-in-the-loop review/approval).
- **AD-03**: async PDF compilation (quota check → Celery enqueue → SafeURLFetcher → tier-based branding/watermark → WeasyPrint render → S3 upload → presigned URL → WebSocket notify).
- **AD-04**: onboarding/multi-tenancy/Midtrans payment/API-key provisioning pipeline.

**Finding state machine**: `OPEN → IN_REVIEW → {REMEDIATED | FALSE_POSITIVE | ACCEPTED_RISK}`, with `REMEDIATED → REOPENED` on regression, `FALSE_POSITIVE → OPEN` on triage correction, `ACCEPTED_RISK → IN_REVIEW` on re-evaluation.

### ERD — "The Lean 11 Tables" (SDD §2.4.1/2.4.2)

`users`, `workspaces`, `workspace_members` (role: MANAGER/PENTESTER/VIEWER), `subscriptions` (tier FREE/PRO/ENTERPRISE, Midtrans fields), `api_keys` (SHA-256 hash), `projects` (target_scope, roe_start_date/roe_end_date TIMESTAMPTZ + timezone), `findings` (dedup_hash UNIQUE, cvss fields, nullable target_port, endpoint_path, is_quarantined, is_curated_for_report, optimistic-lock `version` wired as SQLAlchemy `version_id_col`, created_at), `proofs_of_concept` (AES-256-GCM encrypted_raw_evidence + iv_nonce + auth_tag + key_version, reproduction_steps as a JSON array), `ai_narratives` (tokens_consumed, is_fallback, approval_status), `reports` (storage_path, watermark_applied), `audit_logs` (monthly range-partitioned, composite PK `(id, created_at)`, **no FK on `workspace_id`** so rows outlive a purged workspace per SRS UC-04 E2 — partitions provisioned by `create_audit_log_partition(date)`).

Design deliberately avoids a separate CWE table (loaded in-memory from `cwe_catalog.json`) and a `refresh_tokens` table (stateless revocation via `users.token_version`).

**Security architecture**: STRIDE threat model + mitigation matrix; TLS 1.3 everywhere; CSP with nonces; strict CORS; custom Safe URL Fetcher anti-SSRF for WeasyPrint (blocks private/loopback/link-local IP ranges and non-http(s) schemes — SDD §2.5.4).

**API contracts** (SDD §2.6, OpenAPI 3.1): Unified Vulnerability Finding schema for ingestion; batch ingest `POST /api/v1/workspaces/{w_id}/projects/{p_id}/findings/batch` (Idempotency-Key header, 50/batch Free-tier cap → `HTTP 413`); manual finding entry; AI narrative generation; PDF compile (`HTTP 202` + job polling, `HTTP 307` presigned-URL redirect on download); auth (register/login, Bearer JWT, `expires_in: 86400`); Midtrans checkout/webhook (SHA-512 signature); `StandardErrorEnvelope` (RFC 9110-style: status/code/message/details/timestamp) wraps all errors.

## 3. FASE 0–7 Roadmap (PLAN.md)

Overall progress: **Complete (8/8)** — docs + FASE 0 through FASE 7 done, drift items (#1–#8) resolved and standardized to English UI/backend strings, quality gates clean, and Live Full-Stack E2E (6-container Docker stack + live PostgreSQL 16 semantics + CLI + Mailpit + MinIO + WeasyPrint 70.0 + Gemini `gemini-3-flash-preview` + Midtrans SHA-512 webhook + Vue 3 SPA browser walkthrough) verified on 2026-11-20.

| Phase | Scope | Status |
|---|---|---|
| **FASE 0** | Monorepo scaffolding: `uv` workspace (`apps/api`, `apps/cli`, `packages/contracts`), directory structure, `docker-compose.yml` (Postgres 16, Redis 7.2, MinIO, Mailpit, API, Celery worker), ruff/mypy/bandit/pytest config, `scripts/check_quality.py`, `scripts/dev.py` | **Done** |
| **FASE 1** | Pydantic V2 shared contracts (`packages/contracts/vulnflow_contracts/`): admin_schemas, ai_schemas, auth_schemas, billing_schemas, error_envelope, finding_schemas, report_schemas, workspace_schemas | **Done** (historical FASE 1 baseline: 35 tests, 94.3% coverage; expanded with workspace & admin schemas) |
| **FASE 2** | Database layer — 11 SQLAlchemy 2.0 models, Alembic migrations, AES-256-GCM crypto helper, seeder | **Done** (59 unit tests + 11 live `test_postgres_semantics.py` tests verified against PostgreSQL 16) |
| **FASE 3** | Domain/security engines — DeduplicationService, CVSSCalculator, ScopeEnforcer, PromptSanitizationService, DeterministicFallbackEngine, SafeURLFetcher | **Done** (120 test cases, 96.7% coverage; CVSS formula hand-verified against 3 reference vectors; SafeURLFetcher verified against the exact IPv4-mapped-IPv6 gap flagged in the FASE-2 audit) |
| **FASE 4** | FastAPI routers (Admin, Auth, Workspace/Project, Ingest, Triage, AI, Report, Billing) + Celery worker, global exception handling | **Done, production-hardened** (2 CRITICAL + 16 HIGH audit findings fixed and independently re-verified; `render_html_to_pdf` updated with `_WeasyPrintSafeFetcher` for WeasyPrint 70.0 `URLFetcherResponse` compatibility; universal TOTP MFA enforced at `/auth/login`; S3 logo embedding & English PDF/email standardization verified live) |
| **FASE 5** | CLI agent — `configure`, `setup-tools` (cross-platform Nuclei binary download), `scan`, `push` (idempotent chunked upload) | **Done** (`tests/cli/`, `tests/core/`, `tests/api/`; live CLI `configure`/`status`/`push --type nuclei` with `Idempotency-Key` & `dedup_hash` deduplication verified against Docker API) |
| **FASE 6** | Web Dashboard SPA (Vue 3 Composition API + TypeScript + Vite + Tailwind CSS) — dual-purpose: 5 public unauthenticated routes (`/`, `/about`, `/solutions`, `/solutions/:id`, `/contact`) + `/app/*` authenticated dashboard + `/app/admin` Superadmin console | **Done** (`vue-tsc --noEmit` 0 errors, clean `vite build`, live browser walkthrough passed with 0 console/page errors) |
| **FASE 7** | QA: unit/integration tests, 18 EC-xx resilience test suite (`tests/test_resilience/`), final quality gates, and Full-Stack Live E2E sign-off | **Done** (18/18 EC resilience test modules passing, 11/11 live PostgreSQL semantics tests passing, full-stack E2E + browser verification complete 2026-11-20) |

**Quality gate scoping (PLAN.md §4.1)**: Ruff/Mypy/Bandit/pip-audit are **always** zero-tolerance from FASE 0 onward. Pytest coverage is evaluated *proportionally* (only existing modules) through FASE 0–6; the hard 85% coverage + all-18-EC-tests gate is enforced at FASE 7.3 via `--final` mode.

Commit convention example: `feat(contracts): implement finding schemas according to SDD 2.6.1`, `test(resilience): add test for EC-15 pdf double click distributed lock`.

## 4. The 18 Edge Cases (EC-01..EC-18)

Each has a dedicated test module in `tests/test_resilience/` (`test_ec01_...` through `test_ec18_...`):

1. **EC-01** — Multi-workspace context confusion: CLI reads `active_workspace_id` from local `config.json`; violation → `403`.
2. **EC-02** — Invitation token (7-day signed JWT) expires before invitee registers.
3. **EC-03** — Sole owner tries to delete account while projects active → orphaned workspace; blocked with `409 Conflict`, requires ownership transfer first. Backed at the DB level by `workspace_members.user_id` having NO ACTION (not CASCADE, which silently orphaned the workspace); `projects.lead_pentester_id` is `ON DELETE SET NULL`.
4. **EC-04** — Nested subdomains wrongly flagged out-of-scope; mitigated by FQDN normalization in `ScopeEnforcer`.
5. **EC-05** — Timezone differences cause premature ROE expiry; mitigated via `TIMESTAMPTZ` + project-level `timezone` column. NB: the SQLite unit lane silently drops `tzinfo`, so any datetime-comparison logic must also be covered by `tests/models/test_postgres_semantics.py` (opt-in via `TEST_DATABASE_URL`).
6. **EC-06** — Scanner interrupted mid-run (`Ctrl+C`) corrupts JSON; mitigated by streaming JSONL/NDJSON parser with per-line try/except.
7. **EC-07** — Network drop mid chunked-upload causes silent data loss/duplication; mitigated via per-fragment `Idempotency-Key` (`file_hash:chunk_index`) + HTTPX 3x retry backoff.
8. **EC-08** — Dedup hash formula ignoring endpoint path merges distinct findings; fixed via `dedup_hash = SHA256(project_id + cwe_id + host + port + endpoint_path)`.
9. **EC-09** — Non-network findings have null port; `target_port` must be nullable, renders "N/A", no crash.
10. **EC-10** — Free-tier batch of 52 findings exceeds 50-item cap → `HTTP 413` + CLI interactive prompt to upload top 50 only.
11. **EC-11** — Two auditors edit same finding concurrently; mitigated via optimistic locking (`version` column registered as `version_id_col`, so the UPDATE carries `WHERE version = :old`) → `409 Conflict`. A Python-side version comparison alone is a TOCTOU race, not a lock.
12. **EC-12** — `FALSE_POSITIVE` finding stays checked for report; backend force-sets `is_curated_for_report = false`.
13. **EC-13** — Malicious banner text causes indirect prompt injection; mitigated via sanitizer regex + system-instruction separation.
14. **EC-14** — LLM quota exhausted (`429`)/timeout; mitigated via Deterministic In-Memory Fallback Engine (`cwe_catalog.json`, O(1) lookup).
15. **EC-15** — User double-clicks "Export PDF"; mitigated via Redis distributed lock (`lock:report:{id}`, 10s TTL) → returns same job id.
16. **EC-16** — WeasyPrint worker OOM/crash ("PDF bomb"); Celery `on_failure` refunds quota, sets job `FAILED`.
17. **EC-17** — S3 presigned download URL expires after 15 min; proxy endpoint regenerates fresh URL via `HTTP 307` redirect.
18. **EC-18** — Midtrans sends duplicate webhook callbacks; handler checks `payment_status == 'SETTLEMENT'` before incrementing quota (idempotency).

## 5. Shared Pydantic Contracts (`packages/contracts/vulnflow_contracts/`)

All 8 modules exist, Pydantic V2, `ConfigDict(extra="forbid")` by default (one deliberate exception noted below), `StrEnum`-based enums, modern `X | None` typing:

- **`admin_schemas.py`**: `WorkspaceTokenUsage`, `AITelemetryResponse`, `AdminUserSummary`, `SuspendUserRequest`, `SpendCeilingUpdateRequest` (FR-ADM / UC-17..19 Superadmin telemetry & governance).
- **`error_envelope.py`**: `ErrorCode` enum (AUTHENTICATION_FAILED, QUOTA_EXHAUSTED, BATCH_LIMIT_EXCEEDED, etc.), `ErrorDetail`, `StandardErrorEnvelope`.
- **`finding_schemas.py`**: `Severity`, `CVSSVersion` (3.1/4.0), `Protocol`, `SourceTool` (nmap/nuclei/manual), `FindingStatus` (incl. REOPENED), `ProofOfConceptSchema`, `UnifiedVulnerabilityFinding` (incl. `endpoint_path`, added for EC-08), `ScanMetadata`, `BatchIngestRequest`/`Response`, `ManualFindingRequest`/`Response`.
- **`auth_schemas.py`**: Password complexity validator (8–128 chars, upper/lower/digit/special, null-byte rejection), `WorkspaceRole` enum (**MANAGER/PENTESTER/VIEWER**), `RegisterRequest` (incl. `invitation_token`), `LoginRequest`, `UserDTO`, `WorkspaceMembership`, `RegisterResponse`, `TokenResponse` (Bearer, `expires_in: 86400` = 24h, stateless via `token_version`).
- **`ai_schemas.py`**: `AINarrativeRequest`, `RemediationItem`, `NarrativeContent` (executive_summary/business_impact/remediations), `AINarrativeResponse` (incl. `is_fallback: bool = False`, for EC-14/UC-11b).
- **`report_schemas.py`**: `ReportJobStatus` enum, `ThemeOptions`, `CompilePDFRequest`, `CompilePDFAcceptedResponse`, `ReportJobStatusResponse`, `ReportDownloadResponse` (EC-17 support).
- **`billing_schemas.py`**: `SubscriptionTier` (PRO/ENTERPRISE — FREE isn't purchasable), `MidtransTransactionStatus`, `MidtransCheckoutRequest`/`Response`, `MidtransWebhookPayload` — deliberately uses `extra="ignore"` (external-system payload), case-insensitive hex signature regex.
- **`workspace_schemas.py`**: Workspace, member, invitation, project, API key, and audit log contracts.

Tests: `tests/contracts/test_schemas.py`, 35 tests, round-trips SDD example JSON plus negative-validation cases (malformed CWE, out-of-range port, weak password, un-normalized Midtrans `gross_amount`). Contracts package coverage 100%.

## 6. Audit Findings (DOCS/AUDIT_FINDINGS.md) — All Resolved

A pre-FASE-2 audit found **16 issues (4 HIGH, 8 MEDIUM, 4 LOW)**; the doc's own status line marks all 16 as verified-fixed as of 2026-10-20 (commit `7d7da87`).

- **HIGH-01**: Redis healthcheck used `$$REDIS_PASSWORD` with no `environment:` block → always unhealthy. Fixed.
- **HIGH-02**: RBAC enum conflict (`OWNER` in contracts vs. `MANAGER` in DB dictionary). Fixed — unified to MANAGER/PENTESTER/VIEWER.
- **HIGH-03**: Missing `endpoint_path` field needed for EC-08 dedup hash. Fixed.
- **HIGH-04**: AI system-prompt JSON schema mismatched `NarrativeContent`; missing `is_fallback`. Fixed.
- **MED-01..08**: py.typed marker / mypy overrides for untyped 3rd-party libs, `check_quality.py` robustness (uv PATH fallback, pytest output not swallowed, coverage.json staleness, ruff scope), DB dictionary naming drift, Midtrans webhook over-strictness, password DoS limits, SSRF/Bandit issues in reference snippets, JWT TTL doc conflict (SRS's old 15-min cookie narrative superseded by SDD's 24h Bearer token). All marked fixed.
- **LOW-01..04**: Git hygiene, MinIO version pinning (`RELEASE.2025-04-22T22-12-26Z`), SDD TOC/heading cleanup, minor cross-doc inconsistencies (Pro quota, invitation TTL, HTTP 422 vs 413) — canonical values that won: 30 reports/Pro, 7-day invitation TTL, HTTP 413 for batch limit.

This audit doc is a **point-in-time artifact** explaining *why* contracts look the way they do — not a live backlog.

## 7. Code Quality Standards (root `pyproject.toml` + PLAN.md §2)

- **Package manager**: `uv` workspace (`apps/api`, `apps/cli`, `packages/contracts`); Python `>=3.12`.
- **Ruff**: `target-version="py312"`, line-length 100, rules `E,F,W,I,UP,B,C4,SIM` (no `D`/pydocstyle — comments only when non-obvious, not mandatory docstrings). Zero-tolerance.
- **Mypy**: `strict = true`, `pydantic.mypy` plugin, ignores missing imports for `boto3.*`, `botocore.*`, `celery.*`, `weasyprint.*`. Zero errors required. `tests/` and `migrations/` excluded from strict typing.
- **Bandit**: SAST, excludes `tests`, `migrations`, `.venv`; 0 High/Medium tolerance.
- **pip-audit**: 0 known CVEs in dependencies.
- **Pytest/coverage**: `testpaths=["tests"]`, custom `resilience` marker for EC-01..18; the 85% threshold is enforced progressively by `scripts/check_quality.py`, not the static pytest config.
- **Frontend (planned, FASE 6)**: ESLint (`typescript-eslint` + `eslint-plugin-vue`, Composition API rules), Prettier + `prettier-plugin-tailwindcss`, `vue-tsc --noEmit --strict`.
- **Single quality gate**: `uv run python scripts/check_quality.py` runs Ruff → Mypy → Bandit → Pytest+coverage → pip-audit in sequence; `--final` flag (FASE 7.3) hard-enforces 85% coverage + all 18 EC tests passing.

## 8. Risks / Things to Flag for Upcoming Phases

1. **Documentation vs. code drift risk persists structurally** — SRS/SDD/PLAN/EDGE_CASES are four large, independently-versioned docs that have already needed multiple patch revisions to stay consistent. Double-check current doc wording before building on it; don't assume internal consistency.
2. ~~**FASE 2 is the next milestone...**~~ Resolved 2026-10-22: 11 SQLAlchemy models implemented and diffed against SDD §2.4.2 field-by-field; migration applied and seeder verified against real PostgreSQL 16 (not just SQLite unit tests). One real-world gap SDD doesn't mention: PostgreSQL requires the partition key column in the primary key of a RANGE-partitioned table, so `audit_logs` uses a composite PK `(id, created_at)` instead of SDD's literal single-column `id` PK — and a partitioned table with zero child partitions rejects every INSERT, so an `audit_logs_default` DEFAULT partition was added in the migration. **Update 2026-10-25**: the DEFAULT-only state turned out to be a real bug, not just "deferred" — once any row lands in the default partition, Postgres permanently refuses to attach real monthly partitions. Fixed via migration `d4a7f1c93b28` (monthly partitions + `create_audit_log_partition(date)` helper), see `DOCS/AUDIT_FINDINGS.md` §5 F4-HIGH-05.
3. ~~**CWE fallback catalog doesn't exist yet**~~ Resolved 2026-10-22: `app/data/cwe_catalog.json` created with 7 curated CWE entries + an `UNKNOWN` catch-all default, loaded via `DeterministicFallbackEngine` (`app/domain/fallback.py`, `lru_cache`-backed O(1) lookup).
4. ~~**Reference code snippets in the docs...**~~ `SafeURLFetcher` (`app/services/safe_fetcher.py`) implemented using `ipaddress` properties (`is_private`, `is_loopback`, `is_link_local`, `is_reserved`, `is_unspecified`, `is_multicast`, `ipv4_mapped`) instead of a manual CIDR allowlist, and verified to block the exact gap the audit flagged (`::ffff:127.0.0.1`). The DNS-rebinding gap found in this fix (risk formerly tracked as #11) is now resolved — see below. The `ensure_tools_installed()` CLI snippet (FASE 5.3) is also now resolved (2026-11-01): `apps/cli/vulnflow/tool_provisioner.py` uses `httpx` (not `urllib.request`, avoiding Bandit B310) and extracts only the one exact, hardcoded binary member name from the archive (avoiding the B202 path-traversal pattern the snippet itself warned about).
5. ~~**`apps/web` is completely absent from the filesystem...**~~ **Resolved (FASE 6 & 2026-11-20 UI/UX refinement + drift cleanup):** `apps/web` is fully implemented using Vue 3 + TypeScript + Vite + Tailwind CSS, delivering both the 5 public marketing routes (`/`, `/about`, `/solutions`, `/solutions/:id`, `/contact`) and the authenticated SaaS workspace (`/app/*`, including `/app/admin` console). All UI copy and backend user-facing messages are standardized in English, CLI drawer snippets emit `--token` / `--workspace` / `--type nuclei` without `/api/v1`, Vite proxies `/health`, and live browser walkthrough passed with 0 console/page errors.
6. ~~**FASE 2 (DB layer) and FASE 3 (domain/security engines) are done**; no FastAPI routers or Celery worker exist yet...~~ Resolved 2026-10-24: all 8 FASE 4 sub-phases built, and the FASE 3 modules are now actually wired in — `ScopeEnforcer` into `IngestRouter` (sets `findings.is_quarantined`), `DeduplicationService`/`CVSSCalculator`/`crypto.encrypt_poc` into the batch-ingest path, `PromptSanitizationService`/`DeterministicFallbackEngine` into `AIGhostwriterService` behind `AIRouter`, and `SafeURLFetcher` (wrapped by `_WeasyPrintSafeFetcher` in `report_renderer.py` for WeasyPrint 70.0) is wired into the Report worker's HTML rendering path.
7. ~~**CLI is a Typer stub**~~ Resolved 2026-11-01 (FASE 5): all four real subcommands (`configure`, `setup-tools`, `scan`, `push`) are implemented, TDD, 62 new tests. `push` also closed a backend gap found while building it — see risk #13b below.
8. ~~**`tests/test_resilience/` is empty...**~~ **Resolved (FASE 7):** All 18 dedicated EC test files (`test_ec01_...` through `test_ec18_...`) exist under `tests/test_resilience/` and pass cleanly.
9. **Enforcement asymmetry (FASE 0-6 vs. `--final`)** (PLAN.md §4.1): lint/type/security gates were zero-tolerance from day one, while full EC coverage enforcement is gated via `scripts/check_quality.py --final`.
10. **Midtrans integration has two distinct flows** — a lead-gen estimator/preview on the public `/contact` booking page (where `assetCount <= 10` selects Free plan `Rp 0`) and the real subscription billing flow in `/app/billing`. Note: `BillingRouter` implements the real flow (`PRO` tier upgrade; `ENTERPRISE` is sales-led, rejected with `422`).
11. ~~**`SafeURLFetcher` has a known, unfixed DNS-rebinding gap**~~ Resolved 2026-10-24 (FASE 4.7, not deferred further): `safe_fetcher.py` rewritten to self-fetch via `httpx` directly against the pinned/already-validated IP — one DNS resolution only, never two — while preserving the original hostname via the `Host` header and `sni_hostname` SNI extension. Verified with an `httpx.MockTransport` test asserting the actual outbound request targets the pinned IP, not a re-resolved one.
12. ~~A ReDoS was found and fixed in `sanitizer.py`~~ Resolved 2026-10-22: the hostname-redaction regex used a nested quantifier vulnerable to catastrophic/quadratic backtracking (measured 8-34s on a 40k-char adversarial payload — directly exploitable since `sanitize_text` processes attacker-controlled scanner banner text per EC-13's own threat model). Fixed with a flat O(n) regex + Python-side validation callback; verified <0.01s on the same payload, with 2 new permanent timing-regression tests. The other 3 regexes in the module were stress-tested too and are linear.
13a. ~~**TOP RISK, read before touching FASE 4 code or deploying it**: a 7-agent post-implementation review (2026-10-24) found 2 CRITICAL cross-tenant IDOR bugs... 12 HIGH remain unfixed...~~ **Resolved 2026-11-01.** Everything this item described as open (both CRITICALs, all 16 HIGH, all 25 MEDIUM, all 24 LOW) was in fact fixed in a session between 2026-10-25 and 2026-11-01 that wasn't reflected back into this doc at the time — independently re-verified on 2026-11-01 by reading the actual fixed code (not by trusting the audit doc's own "100% DIPERBAIKI" claim): `triage.py`/`ai.py` now check `Project.workspace_id == workspace_id` before touching a finding; Midtrans signature verification is fail-closed and `gross_amount` is validated against the tier price; `authenticate_user` checks `User.status` and `token_version`; `celery_app` registers `report_worker` tasks; `sanitize_text` is wired into `ai_ghostwriter.py` before any LLM call. Full detail in `DOCS/AUDIT_FINDINGS.md` §5.

13b. **New during FASE 5**: building `vulnflow push` surfaced that `Idempotency-Key` (EC-07) had never actually been wired into `routers/ingest.py` — the CLI could send the header (per SDD §2.6.1.2) but the backend silently ignored it, so a network retry of a chunk would be fully reprocessed rather than short-circuited. Fixed 2026-11-01 via a Redis-backed per-request cache keyed on `(workspace_id, project_id, idempotency_key)`, gated behind a lazy `get_redis_client_factory()` so routes that never receive this header still don't require `REDIS_URL` to be configured. See `DOCS/AUDIT_FINDINGS.md` §6 (`F5-GAP-01`).
14. **Live Full-Stack E2E Verification Completed (2026-11-20)**:
   - Verified against the full 6-container `docker-compose.yml` stack (`vulnflow-postgres`, `vulnflow-redis`, `vulnflow-minio`, `vulnflow-mailpit`, `vulnflow-api`, `vulnflow-worker`):
     - **PostgreSQL 16 Semantics**: `11/11` `tests/models/test_postgres_semantics.py` passed against live `vulnflow_test` DB.
     - **Auth, Mailpit & Universal TOTP**: Registered E2E auditor (`e2e.auditor@vulnflow.local`), verified English invitation/password-reset emails delivered to Mailpit (`http://127.0.0.1:8025`), and verified universal TOTP MFA challenge + `/app/admin` access for Superadmin `admin@vulnflow.local`.
     - **CLI & MinIO & Celery + WeasyPrint 70.0**: Verified live `vulnflow configure`, `status`, and `push --type nuclei` (`Idempotency-Key` replay + `dedup_hash` deduplication), manual PoC + PNG screenshot upload to MinIO, and fixed WeasyPrint 70.0's `URLFetcherResponse` contract (`_WeasyPrintSafeFetcher`) so PRO white-label PDFs with S3 custom PNG logos + CVSS SVG radar + live Gemini narrative compile end-to-end (`33,847` bytes `%PDF-`).
     - **Gemini AI & Admin Telemetry**: Switched default model from deprecated `gemini-2.0-flash`/`gemini-2.5-flash` (AI Studio HTTP 404 for new keys) to `gemini-3-flash-preview` (`timeout=45.0`); live narrative generation succeeded (`1,123`/`1,273` tokens, `is_fallback=False`) and `/app/admin` displayed live workspace AI token telemetry (`2,396` total tokens).
     - **Midtrans Sandbox Billing Note**: Live SHA-512 signed webhook cleanly upgraded the workspace to `PRO` (`monthly_report_quota=30`) with idempotent replay; however, upstream `POST https://app.sandbox.midtrans.com/snap/v1/transactions` returned `403 {"error":"Access denied"}` on the configured sandbox merchant key (while `GET /v2/{id}/status` accepted the key with `200`), indicating a sandbox merchant-account permission/activation setting in Midtrans Dashboard rather than an application code defect.
     - **Live Browser Walkthrough**: Executed full Playwright walkthrough across public showcase routes, authenticated workspace routes, and Superadmin `/app/admin` on `http://localhost:5173` with `0` console errors, `0` uncaught page errors, `0` unexpected `>= 500` responses, and `HTTP 200` MinIO image loads.

## Key File Paths

- `DOCS/SRS.md`, `DOCS/SDD.md`, `DOCS/EDGE_CASES_AND_RESILIENCE.md`, `DOCS/PLAN.md`, `DOCS/AUDIT_FINDINGS.md`, `DOCS/PROJECT_CONTEXT.md`
- `packages/contracts/vulnflow_contracts/{admin_schemas,ai_schemas,auth_schemas,billing_schemas,error_envelope,finding_schemas,report_schemas,workspace_schemas}.py`
- `tests/contracts/test_schemas.py`
- `apps/api/app/core/{database,crypto,seeder,migration_filters,security,exceptions,dependencies,midtrans_signature}.py`, `apps/api/app/main.py`
- `apps/api/app/models/{base,user,workspace,workspace_member,subscription,api_key,project,finding,proof_of_concept,ai_narrative,report,audit_log}.py`
- `apps/api/migrations/` (Alembic — `env.py` wired to `app.models.Base.metadata` + `DATABASE_URL`)
- `apps/api/app/domain/{deduplication,cvss,scope,sanitizer,fallback,ai_ghostwriter}.py`
- `apps/api/app/services/{safe_fetcher,gemini_adapter,redis_client,s3_storage,report_renderer,midtrans_adapter,email_service}.py`
- `apps/api/app/routers/{admin,ai,auth,billing,ingest,projects,reports,triage,workspaces}.py`
- `apps/api/app/workers/{celery_app,report_worker}.py`
- `apps/api/app/data/cwe_catalog.json`
- `apps/cli/vulnflow/main.py`
- `apps/web/` (Vue 3 + TypeScript + Vite SPA)
- `tests/{contracts,core,models,domain,services,api,cli,test_resilience}/`
- `scripts/{check_quality,dev}.py`
- `pyproject.toml` (root)
- `docker-compose.yml`
- `.env.example`
