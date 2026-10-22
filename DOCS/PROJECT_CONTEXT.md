# VulnFlow AI — Full Project Context

> Snapshot date: 2026-10-22. FASE 0-2 complete (monorepo scaffolding, Pydantic contracts, SQLAlchemy 2.0 database layer).
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

`users`, `workspaces`, `workspace_members` (role: MANAGER/PENTESTER/VIEWER), `subscriptions` (tier FREE/PRO/ENTERPRISE, Midtrans fields), `api_keys` (SHA-256 hash), `projects` (target_scope, roe_start_date/roe_end_date TIMESTAMPTZ + timezone), `findings` (dedup_hash UNIQUE, cvss fields, nullable target_port, endpoint_path, is_quarantined, is_curated_for_report, optimistic-lock `version`), `proofs_of_concept` (AES-256-GCM encrypted_raw_evidence + iv_nonce + auth_tag + key_version), `ai_narratives` (tokens_consumed, is_fallback, approval_status), `reports` (storage_path, watermark_applied), `audit_logs` (monthly range-partitioned).

Design deliberately avoids a separate CWE table (loaded in-memory from `cwe_catalog.json`) and a `refresh_tokens` table (stateless revocation via `users.token_version`).

**Security architecture**: STRIDE threat model + mitigation matrix; TLS 1.3 everywhere; CSP with nonces; strict CORS; custom Safe URL Fetcher anti-SSRF for WeasyPrint (blocks private/loopback/link-local IP ranges and non-http(s) schemes — SDD §2.5.4).

**API contracts** (SDD §2.6, OpenAPI 3.1): Unified Vulnerability Finding schema for ingestion; batch ingest `POST /api/v1/workspaces/{w_id}/projects/{p_id}/findings/batch` (Idempotency-Key header, 50/batch Free-tier cap → `HTTP 413`); manual finding entry; AI narrative generation; PDF compile (`HTTP 202` + job polling, `HTTP 307` presigned-URL redirect on download); auth (register/login, Bearer JWT, `expires_in: 86400`); Midtrans checkout/webhook (SHA-512 signature); `StandardErrorEnvelope` (RFC 9110-style: status/code/message/details/timestamp) wraps all errors.

## 3. FASE 0–7 Roadmap (PLAN.md)

Overall progress: **~3/8 complete** — docs + FASE 0 + FASE 1 + FASE 2 done; FASE 3–7 not started.

| Phase | Scope | Status |
|---|---|---|
| **FASE 0** | Monorepo scaffolding: `uv` workspace (`apps/api`, `apps/cli`, `packages/contracts`), directory structure, `docker-compose.yml` (Postgres 16, Redis 7.2, MinIO), ruff/mypy/bandit/pytest config, `scripts/check_quality.py` | **Done** |
| **FASE 1** | Pydantic V2 shared contracts (`packages/contracts/vulnflow_contracts/`): error_envelope, finding_schemas, auth_schemas, ai_schemas, report_schemas, billing_schemas | **Done** (35 tests, 94.3% coverage) |
| **FASE 2** | Database layer — 11 SQLAlchemy 2.0 models, Alembic migrations, AES-256-GCM crypto helper, seeder | **Done** (59 tests, 97.3% coverage; migration applied + seeder verified against real PostgreSQL 16) |
| **FASE 3** | Domain/security engines — DeduplicationService, CVSSCalculator, ScopeEnforcer, PromptSanitizationService, DeterministicFallbackEngine, SafeURLFetcher | Not started |
| **FASE 4** | FastAPI routers (Auth, Workspace/Project, Ingest, Triage, AI, Report, Billing) + Celery worker, global exception handling | Not started |
| **FASE 5** | CLI agent — `configure`, `setup-tools` (cross-platform Nuclei binary download), `scan`, `push` (idempotent chunked upload) | Not started |
| **FASE 6** | Web Dashboard SPA (Vue 3 Composition API + Vite + Tailwind + shadcn-vue) — dual-purpose: 5 public unauthenticated routes (`/`, `/about`, `/solutions`, `/solutions/:id`, `/contact`, satisfying the "Desain Web" course rubric with mock data) + `/app/*` authenticated dashboard (5 SDD wireframes) | Not started |
| **FASE 7** | QA: unit/integration tests, 18 EC-xx resilience test suite (`tests/test_resilience/`), final quality gate (`check_quality.py --final`, hard 85% coverage + 18/18 EC tests) | Not started |

**Quality gate scoping (PLAN.md §4.1)**: Ruff/Mypy/Bandit/pip-audit are **always** zero-tolerance from FASE 0 onward. Pytest coverage is evaluated *proportionally* (only existing modules) through FASE 0–6 — a missing `tests/test_resilience/` doesn't fail the build yet. The hard 85% coverage + all-18-EC-tests gate is enforced only at FASE 7.3 via `--final` mode.

Commit convention example: `feat(contracts): implement finding schemas according to SDD 2.6.1`, `test(resilience): add test for EC-15 pdf double click distributed lock`.

## 4. The 18 Edge Cases (EC-01..EC-18)

Each requires a dedicated test file in `tests/test_resilience/` (currently empty, `.gitkeep` only):

1. **EC-01** — Multi-workspace context confusion: CLI reads `active_workspace_id` from local `config.json`; violation → `403`.
2. **EC-02** — Invitation token (7-day signed JWT) expires before invitee registers.
3. **EC-03** — Sole owner tries to delete account while projects active → orphaned workspace; blocked with `409 Conflict`, requires ownership transfer first.
4. **EC-04** — Nested subdomains wrongly flagged out-of-scope; mitigated by FQDN normalization in `ScopeEnforcer`.
5. **EC-05** — Timezone differences cause premature ROE expiry; mitigated via `TIMESTAMPTZ` + project-level `timezone` column.
6. **EC-06** — Scanner interrupted mid-run (`Ctrl+C`) corrupts JSON; mitigated by streaming JSONL/NDJSON parser with per-line try/except.
7. **EC-07** — Network drop mid chunked-upload causes silent data loss/duplication; mitigated via per-fragment `Idempotency-Key` (`file_hash:chunk_index`) + HTTPX 3x retry backoff.
8. **EC-08** — Dedup hash formula ignoring endpoint path merges distinct findings; fixed via `dedup_hash = SHA256(project_id + cwe_id + host + port + endpoint_path)`.
9. **EC-09** — Non-network findings have null port; `target_port` must be nullable, renders "N/A", no crash.
10. **EC-10** — Free-tier batch of 52 findings exceeds 50-item cap → `HTTP 413` + CLI interactive prompt to upload top 50 only.
11. **EC-11** — Two auditors edit same finding concurrently; mitigated via optimistic locking (`version` column) → `409 Conflict`.
12. **EC-12** — `FALSE_POSITIVE` finding stays checked for report; backend force-sets `is_curated_for_report = false`.
13. **EC-13** — Malicious banner text causes indirect prompt injection; mitigated via sanitizer regex + system-instruction separation.
14. **EC-14** — LLM quota exhausted (`429`)/timeout; mitigated via Deterministic In-Memory Fallback Engine (`cwe_catalog.json`, O(1) lookup).
15. **EC-15** — User double-clicks "Export PDF"; mitigated via Redis distributed lock (`lock:report:{id}`, 10s TTL) → returns same job id.
16. **EC-16** — WeasyPrint worker OOM/crash ("PDF bomb"); Celery `on_failure` refunds quota, sets job `FAILED`.
17. **EC-17** — S3 presigned download URL expires after 15 min; proxy endpoint regenerates fresh URL via `HTTP 307` redirect.
18. **EC-18** — Midtrans sends duplicate webhook callbacks; handler checks `payment_status == 'SETTLEMENT'` before incrementing quota (idempotency).

## 5. Shared Pydantic Contracts (`packages/contracts/vulnflow_contracts/`)

All 6 modules exist, Pydantic V2, `ConfigDict(extra="forbid")` by default (one deliberate exception noted below), `StrEnum`-based enums, modern `X | None` typing:

- **`error_envelope.py`**: `ErrorCode` enum (AUTHENTICATION_FAILED, QUOTA_EXHAUSTED, BATCH_LIMIT_EXCEEDED, etc.), `ErrorDetail`, `StandardErrorEnvelope`.
- **`finding_schemas.py`**: `Severity`, `CVSSVersion` (3.1/4.0), `Protocol`, `SourceTool` (nmap/nuclei/manual), `FindingStatus` (incl. REOPENED), `ProofOfConceptSchema`, `UnifiedVulnerabilityFinding` (incl. `endpoint_path`, added for EC-08), `ScanMetadata`, `BatchIngestRequest`/`Response`, `ManualFindingRequest`/`Response`.
- **`auth_schemas.py`**: Password complexity validator (8–128 chars, upper/lower/digit/special, null-byte rejection), `WorkspaceRole` enum (**MANAGER/PENTESTER/VIEWER**), `RegisterRequest` (incl. `invitation_token`), `LoginRequest`, `UserDTO`, `WorkspaceMembership`, `RegisterResponse`, `TokenResponse` (Bearer, `expires_in: 86400` = 24h, stateless via `token_version`).
- **`ai_schemas.py`**: `AINarrativeRequest`, `RemediationItem`, `NarrativeContent` (executive_summary/business_impact/remediations), `AINarrativeResponse` (incl. `is_fallback: bool = False`, for EC-14/UC-11b).
- **`report_schemas.py`**: `ReportJobStatus` enum, `ThemeOptions`, `CompilePDFRequest`, `CompilePDFAcceptedResponse`, `ReportJobStatusResponse`, `ReportDownloadResponse` (EC-17 support).
- **`billing_schemas.py`**: `SubscriptionTier` (PRO/ENTERPRISE — FREE isn't purchasable), `MidtransTransactionStatus`, `MidtransCheckoutRequest`/`Response`, `MidtransWebhookPayload` — deliberately uses `extra="ignore"` (external-system payload), case-insensitive hex signature regex.

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
2. ~~**FASE 2 is the next milestone...**~~ Resolved 2026-10-22: 11 SQLAlchemy models implemented and diffed against SDD §2.4.2 field-by-field; migration applied and seeder verified against real PostgreSQL 16 (not just SQLite unit tests). One real-world gap SDD doesn't mention: PostgreSQL requires the partition key column in the primary key of a RANGE-partitioned table, so `audit_logs` uses a composite PK `(id, created_at)` instead of SDD's literal single-column `id` PK — and a partitioned table with zero child partitions rejects every INSERT, so an `audit_logs_default` DEFAULT partition was added in the migration (monthly partition provisioning remains deferred to a later scheduled job, per SDD §2.4.4's "otomatis setiap pergantian bulan").
3. **CWE fallback catalog (`app/data/cwe_catalog.json`) doesn't exist yet** and its schema isn't specified beyond "curated remediation narratives per CWE" — original content creation needed for FASE 3.5. This is now the next-highest-leverage open risk.
4. **Reference code snippets in the docs are explicitly illustrative, not production-ready** — e.g. EDGE_CASES_AND_RESILIENCE.md's own `ensure_tools_installed()` snippet violates Bandit B310/B202; SDD's `safe_url_fetcher` snippet fails mypy --strict and has SSRF gaps (IPv4-mapped IPv6, missing 0.0.0.0/8 and fe80::/10 blocks). Rewrite with `httpx` (not `urllib.request`), validate zip member paths before extraction, use `ipaddress` properties (`is_private`, `is_loopback`, `is_link_local`, `ip.ipv4_mapped`) instead of a manual CIDR allowlist.
5. **`apps/web` is completely absent from the filesystem** — load-bearing for two courses (IPPL dashboard + "Desain Web" rubric). The dual-purpose routing design (public marketing routes with mock data vs. `/app/*` authenticated dashboard) is clear in the docs but unimplemented. The public-route spec lives in an external file `Desweb/DOCS/Dokumentasi_Proyek_Desweb_VulnFlow_AI.docx` one level up from this repo (`IPPL/Desweb/`) — fetch/read before starting FASE 6.
6. **FASE 2 (DB layer) is done**; no FastAPI routers, domain services, or Celery worker exist yet. All of FASE 3–4 is greenfield.
7. **CLI is a Typer stub** — only `--version` works; real subcommands (`configure`, `setup-tools`, `scan`, `push`) don't exist yet (FASE 5).
8. **`tests/test_resilience/` is empty** (just `.gitkeep`) — none of the 18 EC tests exist yet; correctly sequenced last, but represents a large bolus of test-writing work at the end.
9. **Enforcement asymmetry is intentional, not an oversight** (PLAN.md §4.1): lint/type/security gates are zero-tolerance from day one, but coverage/EC-tests are deferred to FASE 7.3 — coverage regressions could silently accumulate through FASE 2–6 without failing CI in the interim.
10. **Midtrans integration has two distinct flows** — a lead-gen "simulator" on the public `/contact` booking page (FASE 6.7) and the real subscription billing flow in the authenticated dashboard (FASE 6.15). Don't conflate them.

## Key File Paths

- `DOCS/SRS.md`, `DOCS/SDD.md`, `DOCS/EDGE_CASES_AND_RESILIENCE.md`, `DOCS/PLAN.md`, `DOCS/AUDIT_FINDINGS.md`
- `packages/contracts/vulnflow_contracts/{error_envelope,finding_schemas,auth_schemas,ai_schemas,report_schemas,billing_schemas}.py`
- `tests/contracts/test_schemas.py`
- `apps/api/app/core/{database,crypto,seeder}.py`
- `apps/api/app/models/{base,user,workspace,workspace_member,subscription,api_key,project,finding,proof_of_concept,ai_narrative,report,audit_log}.py`
- `apps/api/migrations/` (Alembic — `env.py` wired to `app.models.Base.metadata` + `DATABASE_URL`)
- `tests/core/`, `tests/models/`
- `apps/cli/vulnflow/main.py`
- `pyproject.toml` (root)
- `docker-compose.yml`
- `.env.example`
