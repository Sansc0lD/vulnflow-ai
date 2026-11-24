# VulnFlow AI

SaaS platform manajemen kerentanan & asisten pelaporan untuk pentester  mengagregasi hasil pemindaian (Nmap/Nuclei) dari CLI lokal, melakukan triase & kalkulasi CVSS, lalu menyusun laporan PDF dengan bantuan AI yang dijamin tidak pernah menerima data sensitif target (IP, port, PoC mentah).

> Proyek mata kuliah **Implementasi Perancangan Perangkat Lunak (IPPL)**, dikembangkan dengan metodologi **Spec-Driven Development** + **Test-Driven Development**. Frontend web (`apps/web`) juga memenuhi rubrik mata kuliah **Desain Web** (lihat [Lintas Mata Kuliah](#lintas-mata-kuliah-desain-web) di bawah).

## Dokumentasi Lengkap

Spesifikasi mengikat ada di [`DOCS/`](DOCS/), **bukan** di README ini:

| Dokumen                                                             | Isi                                                                        |
|:------------------------------------------------------------------- |:-------------------------------------------------------------------------- |
| [`SRS.md`](DOCS/SRS.md)                                             | Kebutuhan fungsional, use case, NFR (apa yang dibangun)                    |
| [`SDD.md`](DOCS/SDD.md)                                             | Arsitektur C4, ERD, kontrak REST API, wireframe (bagaimana membangunnya)   |
| [`EDGE_CASES_AND_RESILIENCE.md`](DOCS/EDGE_CASES_AND_RESILIENCE.md) | 18 kasus batas (EC-01..EC-18) wajib teruji                                 |
| [`PLAN.md`](DOCS/PLAN.md)                                           | Checklist kerja per fase (FASE 0-7) & standar mutu kode                    |
| [`AUDIT_FINDINGS.md`](DOCS/AUDIT_FINDINGS.md)                       | Catatan audit teknis & riwayat perbaikan lintas fase                       |
| [`PROJECT_CONTEXT.md`](DOCS/PROJECT_CONTEXT.md)                     | Ringkasan konteks arsitektur, progres fase, dan verifikasi live terbaru    |
| [`BROWSER_TESTING_GUIDE.md`](DOCS/BROWSER_TESTING_GUIDE.md)         | Panduan pengujian manual end-to-end semua role di browser                  |
| [`QA_SIGN_OFF.md`](DOCS/QA_SIGN_OFF.md)                             | Snapshot verifikasi mutu (status `v1.0.0` Release Candidate)              |
| [`BETA_RELEASE_PLAN.md`](DOCS/BETA_RELEASE_PLAN.md)                 | Arsip rencana finalisasi beta & checklist validasi pemilik proyek          |

README ini hanya memandu *cara menjalankan* proyek — untuk *keputusan desain/kebutuhan*, selalu rujuk dokumen di atas.

## Tech Stack

| Layer               | Teknologi                                                                                 |
|:------------------- |:----------------------------------------------------------------------------------------- |
| Backend API         | Python 3.12+, FastAPI, SQLAlchemy 2.0, Alembic, Celery + Redis                            |
| PDF & AI & Billing  | WeasyPrint 70.0, `pypdfium2` + `pikepdf` + `segno` + `pyhanko`, Gemini / Ollama, Midtrans |
| Database            | PostgreSQL 16 (tabel partisi `audit_logs`, AES-256-GCM encrypted PoC)                     |
| Object Storage      | MinIO (S3-compatible, logo agency & artefak PDF)                                          |
| Email Dev Sandbox   | Mailpit (`localhost:8025` Web UI / port SMTP `1025`)                                      |
| CLI Agent           | Python 3.12+, Typer, Rich, HTTPX                                                          |
| Web Dashboard       | Vue 3 (Composition API, TypeScript), Vite, Tailwind CSS, `pnpm`, Nginx (prod overlay)     |
| Shared Contracts    | Pydantic V2 (`packages/contracts`, dipakai bersama API & CLI)                             |
| CI & Quality Gates  | GitHub Actions (`.github/workflows/ci.yml`), Ruff, Mypy, Bandit, Pytest, `pip-audit`      |
| Package/Dep Manager | [`uv`](https://docs.astral.sh/uv/) (Python workspace) & `pnpm` (`apps/web`)               |

## Struktur Monorepo

```
vulnflow-ai/
├─ apps/
│  ├─ api/                 # FastAPI backend, Alembic migrations, Jinja2 PDF templates, Celery AI & PDF workers
│  ├─ cli/                 # CLI agent (`vulnflow`)
│  └─ web/                 # Vue 3 + TypeScript SPA + Nginx Dockerfile (`apps/web/Dockerfile`)
├─ packages/
│  └─ contracts/           # Pydantic V2 schemas bersama (`vulnflow_contracts/`)
├─ tests/                  # Suite unit, integrasi, PostgreSQL semantics, dan 18 resilience tests (EC-01..18)
├─ scripts/
│  ├─ dev.py               # Orchestrator dev/test (`up`, `demo`, `migrate`, `server`, `worker`, `status`, `totp`)
│  └─ check_quality.py     # Gerbang mutu satu pintu (lint, type, security, test, audit)
├─ .github/workflows/      # CI pipeline (`ci.yml`: backend-quality, postgres-semantics, frontend-build)
├─ DOCS/                   # SRS, SDD, Edge Cases, Plan, Audit Findings, Project Context, Browser Guide, QA Beta
├─ docker-compose.yml      # 6 container dev stack: postgres, redis, minio, mailpit, api, worker
├─ docker-compose.prod.yml # Overlay production/demo: tambah Nginx `web` (:8080) & Gunicorn `api`
├─ .env.example            # Salin ke .env, isi kredensial sendiri
├─ CHANGELOG.md            # Catatan rilis VulnFlow AI v1.0.0
├─ LICENSE                 # Lisensi MIT
└─ pyproject.toml          # uv workspace root + konfigurasi ruff/mypy/pytest/bandit
```

## Prasyarat

- [Python 3.12+](https://www.python.org/)
- [`uv`](https://docs.astral.sh/uv/getting-started/installation/) — **install lewat installer resmi**, bukan `pip install uv`, agar otomatis masuk PATH.
- [Docker](https://www.docker.com/) + Docker Compose — untuk PostgreSQL, Redis, MinIO, Mailpit, API, dan Celery Worker (termasuk GTK3/Pango/Cairo untuk WeasyPrint).
- Node.js 20+ & `pnpm` — untuk build dan dev server `apps/web`.

## Setup Awal

```bash
# 1. Salin template environment variable, isi dengan kredensial sendiri (GEMINI_API_KEY, MIDTRANS_SERVER_KEY, dll.)
cp .env.example .env

# 2. Nyalakan seluruh 6 container stack (postgres, redis, minio, mailpit, api, worker)
docker compose up -d --build

# 3. Install seluruh dependensi Python workspace (apps/api, apps/cli, packages/contracts)
uv sync --all-packages

# 4. Pastikan CLI terpasang dengan benar
uv run vulnflow --version

# 5. (Jika menjalankan migrasi/seeder secara manual di luar entrypoint container API)
uv run python scripts/dev.py migrate
docker compose exec -T api python -c "from app.core.database import make_engine, make_session_factory, get_database_url; from app.core.seeder import seed_defaults; s = make_session_factory(make_engine(get_database_url()))(); seed_defaults(s)"

# 6. Install & jalankan frontend SPA (http://localhost:5173)
pnpm --dir apps/web install
pnpm --dir apps/web run dev

# 7. (Opsional) Cetak kode TOTP 6-digit terbaru untuk login Superadmin (`admin@vulnflow.local`)
uv run python scripts/dev.py totp
```

> Untuk menjalankan orkestrasi lokal tanpa container API/worker, tersedia `uv run python scripts/dev.py up` atau `uv run python scripts/dev.py demo`. Layanan web dev dapat diakses pada `http://localhost:5173`, Swagger API di `http://127.0.0.1:8000/docs`, Mailpit di `http://localhost:8025`, dan MinIO Console di `http://localhost:9001`.

## Demo / Production 1-Perintah (`docker-compose.prod.yml`)

Untuk menjalankan keseluruhan aplikasi **termasuk Frontend SPA via Nginx + API Gunicorn** tanpa `pnpm dev`:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

- Web SPA & API reverse-proxy tersedia pada `http://localhost:8080`.
- Menghentikan stack overlay: `docker compose -f docker-compose.yml -f docker-compose.prod.yml down`.

## Menjalankan Gerbang Mutu

Wajib dijalankan setelah setiap sub-tugas selesai (lihat [`PLAN.md`](DOCS/PLAN.md) §4) dan otomatis dijalankan oleh GitHub Actions ([`ci.yml`](.github/workflows/ci.yml)):

```bash
uv run python scripts/check_quality.py
```

- **Mode default (FASE 0-6):** Ruff/Mypy/Bandit/pip-audit selalu *zero-tolerance*; coverage test dievaluasi proporsional terhadap kode yang sudah ada.

- **Mode `--final` (FASE 7.3, gerbang akhir):** menegakkan ambang keras 85% coverage + seluruh 18 test resilience (EC-01..EC-18) harus ditemukan dan lolos.

  ```bash
  uv run python scripts/check_quality.py --final
  ```

## Status Proyek

Lihat tracker lengkap di [`PLAN.md`](DOCS/PLAN.md), konteks arsitektur di [`PROJECT_CONTEXT.md`](DOCS/PROJECT_CONTEXT.md), serta panduan QA manual di [`BROWSER_TESTING_GUIDE.md`](DOCS/BROWSER_TESTING_GUIDE.md). Ringkasan saat ini (**Status: `v1.0.0` Release Candidate (`release/v1.0.0`) — Menunggu Konfirmasi CI GitHub Actions & Tag Final**):

- [x] Dokumentasi (`SRS.md`, `SDD.md`, `EDGE_CASES_AND_RESILIENCE.md`, `PLAN.md`) — selesai
- [x] **FASE 0** — Monorepo scaffolding, `docker-compose`, linter/type-checker, `check_quality.py`, CI pipeline — selesai & terverifikasi
- [x] **FASE 1** — Pydantic V2 Shared Contracts — selesai (`admin_schemas`, `auth_schemas`, `ai_schemas`, `billing_schemas`, `error_envelope`, `finding_schemas`, `report_schemas`, `workspace_schemas`)
- [x] **FASE 2** — Database Layer (The Lean 11 Tables + `enterprise_inquiries`, Alembic head `c3d4e5f6a703`) — selesai; migrasi & seeder terverifikasi terhadap PostgreSQL 16 nyata (`test_postgres_semantics.py`)
- [x] **FASE 3** — Domain Core & Security Engines — selesai (`DeduplicationService`, `CVSSCalculator`, `ScopeEnforcer`, `PromptSanitizationService`, `DeterministicFallbackEngine`, `SafeURLFetcher`)
- [x] **FASE 4** — FastAPI Routers & Celery Workers (`ai_worker`, `report_worker`, `pdf_protector`, `ollama_adapter`, `captcha_service`) — selesai & hardened
- [x] **FASE 5** — CLI Agent (`configure`, `setup-tools`, `scan`, `push` dengan `Idempotency-Key` & chunked retry) — selesai
- [x] **FASE 6** — Vue 3 + TypeScript Web SPA (`/`..`/contact`, `/verify/:code?`, `/app/*` workspace, dan `/app/admin` console terisolasi) — selesai
- [x] **FASE 7** — Resilience Test Suite (EC-01..EC-18), 5/5 `--final` Quality Gate (`85.5%` coverage, `0` CVE), Full-Stack Live E2E & Production Nginx Overlay (`v1.0.0` RC terverifikasi lokal, [`CHANGELOG.md`](CHANGELOG.md) & [`LICENSE`](LICENSE) tersedia)

## Lintas Mata Kuliah: Desain Web

`apps/web` sengaja disatukan untuk memenuhi dua mata kuliah sekaligus dalam satu basis kode:

- **Rute Publik** (`/`, `/about`, `/solutions`, `/solutions/:id`, `/contact`, `/verify/:code?`) — rute publik & verifikasi keaslian laporan, memenuhi rubrik wajib mata kuliah Desain Web. Spesifikasi UI/UX lengkapnya ada di `../Desweb/DOCS/Dokumentasi_Proyek_Desweb_VulnFlow_AI.docx` (rujukan mengikat, tidak diduplikasi di `SDD.md`).
- **Rute Terautentikasi** (`/app/*`) — dashboard SaaS VulnFlow AI yang sesungguhnya, untuk mata kuliah IPPL.

Detail lengkap: [`SRS.md`](DOCS/SRS.md) Bab 4.10 (FR-PUB) dan [`SDD.md`](DOCS/SDD.md) §4.2.
