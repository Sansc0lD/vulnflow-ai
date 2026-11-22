# Rencana Finalisasi & Rilis Bersih — VulnFlow AI (`v1.0.0-beta`)

**Status Target:** **Beta / Pre-Release Candidate (`v1.0.0-beta`)**  
**Tanggal Penyusunan:** 23 November 2026  
**Branch Target:** `main` (commit lokal terstruktur — **belum push ke GitHub**)

> [!IMPORTANT]
> Dokumen ini **bukan** penetapan rilis produksi final (`v1.0.0` GA). Seluruh perubahan yang tercakup di rencana ini menargetkan kesiapan **Beta (`v1.0.0-beta`)** pada repositori lokal dengan database bersih. Validasi manual akhir, `git push origin main`, dan penetapan rilis `v1.0.0` GA sepenuhnya berada di tangan pemilik proyek setelah pengecekan langsung selesai.

---

## Ringkasan Keputusan Pemilik Proyek

1. **File Scratch & Panduan Browser:**
   - Tiga file catatan sementara di root repositori (`antislop.md`, `eval_system.md`, `eval_part2.md`) **dipindahkan ke luar repositori** (`..\scratch_notes\`), bukan dihapus permanen, karena berisi catatan pengujian dan path lokal.
   - [`DOCS/BROWSER_TESTING_GUIDE.md`](BROWSER_TESTING_GUIDE.md) **diperbaiki isinya** agar sinkron dengan fitur terbaru lalu **diikutkan ke commit**.
2. **Keadaan Database & Storage Lokal:**
   - Setelah seluruh pengujian otomatis dan verifikasi stack selesai, database PostgreSQL, cache Redis, dan object storage MinIO lokal **direset bersih** (`docker compose down -v`) lalu diisi ulang hanya dengan migrasi Alembic hingga head terbaru dan *default seed* (`admin@vulnflow.local` + template workspace).
3. **Alur Git & Status Rilis:**
   - Perubahan dipisah menjadi **beberapa commit lokal terstruktur** di branch `main` saja.
   - **Tidak ada `git push`** dan **tidak ada tag `v1.0.0` GA** yang dibuat sebelum pemilik proyek melakukan validasi mandiri.

---

## 1. Audit Baseline Terverifikasi (`23 November 2026`)

Berdasarkan pemeriksaan langsung terhadap *working tree* dan tool mutu repositori:

### 1.1 Komponen yang Sudah Lulus / Selesai
- **Dependency CVE Audit (`uv run pip-audit`):** `PASS` (`0` known vulnerabilities); [`pyproject.toml`](../pyproject.toml) dan `uv.lock` sudah mengunci `brotli>=1.2.1`, `dnspython>=2.9.2`, dan `opentelemetry-api>=1.45.2`.
- **Lint & Static Analysis:** `uv run ruff check` (`0` error), `uv run mypy --strict` (`Success: no issues found in 82 source files`), `uv run bandit` (`0` issue), serta `pnpm --dir apps/web exec vue-tsc --noEmit` (`exit 0`).
- **Midtrans Sandbox Checkout (`billing.py`):** Perbaikan panjang `order_id` menjadi `ORD-{workspace_id.hex}-{timestamp}` (**47 karakter**, memenuhi batas maksimal **50 karakter** Midtrans Snap) sudah lulus test unit/integrasi maupun *live checkout* (`HTTP 200`).
- **Fitur Baru di *Working Tree* (Pra-Beta):**
  - Enterprise Sales Inquiry & Lead Capture ([`enterprise_inquiry.py`](../apps/api/app/models/enterprise_inquiry.py), integrasi `/contact` & tab admin).
  - Private VPC LLM adapter ([`ollama_adapter.py`](../apps/api/app/services/ollama_adapter.py)) & background AI worker + prompt cache ([`ai_worker.py`](../apps/api/app/workers/ai_worker.py)).
  - Proteksi PDF Free-tier (rasterize via `pypdfium2`/`Pillow`, lock izin via `pikepdf`), QR verifikasi (`segno`), tanda tangan PAdES opsional (`pyhanko`) di [`pdf_protector.py`](../apps/api/app/services/pdf_protector.py), serta halaman verifikasi publik [`VerifyReport.vue`](../apps/web/src/pages/public/VerifyReport.vue) (`/verify/:code?`).
  - Konteks `tech_stack` proyek dan halaman admin ke-4 (`Workspaces & Plans` di `/app/admin?tab=workspaces`).
  - Dua migrasi Alembic baru (`a1b2c3d4e501` → head `b2c3d4e5f602`).

### 1.2 Blocker yang Wajib Ditutup Menuju `v1.0.0-beta`
1. **Format Kode Ruff:** `uv run ruff format --check` saat ini gagal (`exit 1`) pada **8 file Python**.
2. **Kebersihan Root Repo:** 3 file scratch *untracked* (`antislop.md`, `eval_system.md`, `eval_part2.md`) masih berada di root repo dan merujuk path screenshot lokal.
3. **Sinkronisasi Environment & Docker Worker:** 9+ env var baru di kode backend belum terdokumentasi di [`.env.example`](../.env.example), dan service `worker` di [`docker-compose.yml`](../docker-compose.yml) belum menerima `APP_BASE_URL` / `SMTP_*` seperti service `api`.
4. **Verifikasi Migrasi & Dependensi Image Docker Baru:** Dua migrasi Alembic baru (`a1b2c3d4e501`, `b2c3d4e5f602`) serta dependensi baru di [`apps/api/pyproject.toml`](../apps/api/pyproject.toml) belum diuji via `test_postgres_semantics.py` dan *rebuild* image Docker.
5. **Kemasan Production & CI Pipeline:** Belum tersedia container production `apps/web` + Nginx overlay serta workflow `.github/workflows/ci.yml`.
6. **Sinkronisasi Dokumentasi Beta:** [`DOCS/BROWSER_TESTING_GUIDE.md`](BROWSER_TESTING_GUIDE.md), [`DOCS/QA_SIGN_OFF.md`](QA_SIGN_OFF.md), [`DOCS/PROJECT_CONTEXT.md`](PROJECT_CONTEXT.md), dan [`README.md`](../README.md) belum mencerminkan fitur baru maupun status **`v1.0.0-beta`**.

---

## 2. Tahap Kerja Rinci (Tahap 1 s.d. Tahap 8)

> [!NOTE]
> Seluruh perintah PowerShell di bawah menghindari operator `&&` agar kompatibel dengan Windows PowerShell 5.1 (gunakan `;` atau jalankan per baris).

### Tahap 1 — Pemindahan File Scratch & Formatting Codebase
- [ ] **1.1** Buat folder eksternal di luar repositori (`..\scratch_notes`) dan pindahkan 3 file catatan sementara agar tidak ikut ter-commit, namun tetap tersimpan aman di mesin lokal:
  ```powershell
  New-Item -ItemType Directory -Force -Path ..\scratch_notes
  Move-Item -LiteralPath antislop.md, eval_system.md, eval_part2.md -Destination ..\scratch_notes\
  ```
- [ ] **1.2** Format 8 file Python yang terdeteksi oleh `ruff format --check`:
  - `apps/api/app/domain/ai_ghostwriter.py`
  - `apps/api/app/domain/sanitizer.py`
  - `apps/api/app/routers/ai.py`
  - `apps/api/app/routers/projects.py`
  - `apps/api/app/routers/reports.py`
  - `tests/api/test_enterprise_and_system_upgrades.py`
  - `tests/api/test_workspace_router.py`
  - `tests/services/test_pdf_protector.py`
  ```powershell
  uv run ruff format apps/api/app/domain/ai_ghostwriter.py apps/api/app/domain/sanitizer.py apps/api/app/routers/ai.py apps/api/app/routers/projects.py apps/api/app/routers/reports.py tests/api/test_enterprise_and_system_upgrades.py tests/api/test_workspace_router.py tests/services/test_pdf_protector.py
  ```
- [ ] **1.3** Verifikasi ulang linter & formatter:
  ```powershell
  uv run ruff check apps/api/app apps/cli packages/contracts scripts tests
  uv run ruff format --check apps/api/app apps/cli packages/contracts scripts tests
  ```
- **Kriteria Selesai:** Kedua perintah keluar dengan status `0`, dan 3 file scratch sudah tidak ada di `git status`.

---

### Tahap 2 — Sinkronisasi `.env.example` & `docker-compose.yml` (Dev Stack)
- [ ] **2.1** Perbarui [`.env.example`](../.env.example) untuk mendokumentasikan variabel environment baru (dengan nilai default aman non-rahasia):
  - `LLM_PROVIDER=gemini` *(pilihan: `gemini` | `ollama`)*
  - `GEMINI_FALLBACK_MODEL=gemini-2.5-flash` *(atau fallback model cadangan)*
  - `OLLAMA_BASE_URL=http://127.0.0.1:11434`
  - `OLLAMA_MODEL=llama3.1:8b`
  - `AI_WORKSPACE_RPM_LIMIT=3`
  - `SALES_NOTIFICATION_EMAIL=sales@vulnflow.local`
  - `PDF_SIGNING_CERT_PATH=` *(opsional — path sertifikat PEM untuk PAdES PDF signing)*
  - `PDF_SIGNING_KEY_PATH=` *(opsional — path private key PEM untuk PAdES PDF signing)*
  - `PDF_SIGNING_KEY_PASSPHRASE=` *(opsional — passphrase kunci private PAdES)*
  - Pastikan `CORS_ALLOWED_ORIGINS=http://localhost:5173` ikut terdokumentasi eksplisit di [`.env.example`](../.env.example).
- [ ] **2.2** Periksa `.env` lokal agar tidak kekurangan variabel runtime yang dibutuhkan (tanpa pernah mencetak nilai rahasia ke terminal/log).
- [ ] **2.3** Sinkronkan blok `environment:` service `worker` pada [`docker-compose.yml`](../docker-compose.yml):
  - Tambahkan `- APP_BASE_URL=${APP_BASE_URL:-http://localhost:5173}` agar QR verification link pada PDF yang digenerate Celery menunjuk ke origin web yang benar.
  - Tambahkan `- SMTP_HOST=mailpit`, `- SMTP_PORT=${SMTP_PORT:-1025}`, dan `- SMTP_ENABLED=${SMTP_ENABLED:-true}` agar task background konsisten dengan container `api`.
- [ ] **2.4** Rebuild container `api` dan `worker` agar dependensi baru (`pypdfium2`, `pillow`, `pikepdf`, `pyhanko`, `segno`, `jinja2`, `gunicorn`) di image Docker sinkron dengan `uv.lock`:
  ```powershell
  docker compose up -d --build api worker
  docker compose ps
  docker compose exec -T api alembic -c apps/api/alembic.ini current
  ```
- **Kriteria Selesai:** Container `api` sehat (`healthy`), `worker` berjalan tanpa error import, dan `alembic current` menunjukkan `b2c3d4e5f602 (head)`.

---

### Tahap 3 — Verifikasi Quality Gate Penuh (5/5) & Live PostgreSQL 16 Semantics
- [ ] **3.1** Jalankan gerbang mutu penuh repositori:
  ```powershell
  uv run python scripts/check_quality.py --final
  ```
  Target: **5/5 PASS** (Ruff, Mypy `--strict`, Bandit, Pytest + Branch Coverage $\ge 85\%$ + 18/18 EC resilience suite, `pip-audit` `0` CVE).
- [ ] **3.2** Uji migrasi & keselarasan ORM terhadap PostgreSQL 16 nyata pada database sementara `vulnflow_test`:
  ```powershell
  docker compose exec -T postgres psql -U vulnflow -d postgres -c "DROP DATABASE IF EXISTS vulnflow_test;"
  docker compose exec -T postgres psql -U vulnflow -d postgres -c "CREATE DATABASE vulnflow_test;"
  ```
  Jalankan `uv run pytest tests/models/test_postgres_semantics.py -v` dengan `TEST_DATABASE_URL` menunjuk ke `vulnflow_test` (diambil dari `.env` tanpa mencetak password ke stdout), memastikan migrasi `a1b2c3d4e501` dan `b2c3d4e5f602` menghasilkan `compare_metadata == []`, nol redundant index, serta partisi `audit_logs` tetap utuh. Lalu hapus database sementara:
  ```powershell
  docker compose exec -T postgres psql -U vulnflow -d postgres -c "DROP DATABASE IF EXISTS vulnflow_test;"
  ```
- [ ] **3.3** Uji rendering WeasyPrint + proteksi PDF (`pypdfium2`, `pikepdf`, `segno`, `pillow`) di dalam container Linux `vulnflow-api` agar pustaka native (`GTK3`/`Pango`/`Cairo`) terverifikasi langsung (bukan hanya di-skip di host Windows).
- [ ] **3.4** Jalankan pemeriksaan frontend:
  ```powershell
  pnpm --dir apps/web run type-check
  pnpm --dir apps/web run build
  ```
- **Kriteria Selesai:** Seluruh check backend, PostgreSQL semantics (`11 passed`), container Linux PDF pipeline, `vue-tsc`, dan `vite build` keluar dengan status `0`.

---

### Tahap 4 — Kemasan Production / Demo 1-Perintah (`apps/web` + Nginx Overlay)
**Tujuan:** Menyediakan cara menjalankan keseluruhan stack (Frontend SPA + API + Worker + DB + Redis + MinIO + Mailpit) lewat Docker tanpa mengganggu konfigurasi dev (`docker-compose.yml` + `pnpm dev`).

- [ ] **4.1** Buat `apps/web/.dockerignore` (`node_modules`, `dist`, `.vite`, `*.log`) agar build context frontend ringan.
- [ ] **4.2** Buat `apps/web/Dockerfile` (*multi-stage build*):
  - **Stage 1 (`builder`):** `node:20-alpine`, `corepack enable`, salin `package.json` & `pnpm-lock.yaml`, jalankan `pnpm install --frozen-lockfile`, salin source `apps/web`, lalu `pnpm run build` (menghasilkan `/app/dist`).
  - **Stage 2 (`runtime`):** `nginx:1.27-alpine`, salin `/app/dist` ke `/usr/share/nginx/html`, salin `apps/web/nginx.conf` ke `/etc/nginx/conf.d/default.conf`, expose port `80`, dan tambahkan `HEALTHCHECK` (`wget -qO- http://127.0.0.1/health`).
- [ ] **4.3** Buat `apps/web/nginx.conf`:
  - SPA fallback: `location / { try_files $uri $uri/ /index.html; }` (memastikan rute langsung seperti `/verify/VF-...` atau `/app/admin` tidak 404).
  - Reverse proxy ke API (selaras dengan [`apps/web/vite.config.ts`](../apps/web/vite.config.ts)):
    - `location /api/` → `proxy_pass http://api:8000;` (termasuk `X-Real-IP`, `X-Forwarded-For`, `X-Forwarded-Proto`, serta `proxy_read_timeout 120s` untuk endpoint AI/PDF).
    - `location = /health` → `proxy_pass http://api:8000/health;`.
  - `client_max_body_size 25M;` untuk unggah batch temuan, screenshot PoC, dan logo workspace.
  - Header keamanan standar (`X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, `Referrer-Policy: strict-origin-when-cross-origin`), gzip aktif, dan `Cache-Control` panjang khusus `/assets/`.
- [ ] **4.4** Buat overlay `docker-compose.prod.yml`:
  - Menambahkan service `web` (`vulnflow-web`, port `${WEB_PORT:-8080}:80`, `depends_on: api (condition: service_healthy)`).
  - Menjalankan `api` dengan Gunicorn + `uvicorn.workers.UvicornWorker` (`gunicorn app.main:app -k uvicorn.workers.UvicornWorker -w 2 -b 0.0.0.0:8000`).
  - Menyinkronkan `APP_BASE_URL=${PROD_APP_BASE_URL:-http://localhost:8080}` dan `CORS_ALLOWED_ORIGINS=${PROD_CORS_ALLOWED_ORIGINS:-http://localhost:8080}` pada `api` & `worker`.
- [ ] **4.5** Uji *smoke test* overlay production:
  ```powershell
  docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
  ```
  - Verifikasi `http://localhost:8080/` (`200` HTML SPA), `http://localhost:8080/verify/INVALID` (`200` SPA fallback, bukan 404 Nginx), `http://localhost:8080/health` (`200 {"status":"ok"}`), dan proxy `POST /api/v1/auth/login`.
  - Setelah uji selesai, kembalikan ke stack dev (`docker compose down` → dilanjutkan di Tahap 7 saat reset bersih).

---

### Tahap 5 — GitHub Actions CI Pipeline (`.github/workflows/ci.yml`)
- [ ] **5.1** Buat `.github/workflows/ci.yml` dengan trigger `push` & `pull_request` pada branch `main`, berisi 3 job paralel yang terisolasi:
  1. **`backend-quality`** (`ubuntu-latest`, Python `3.12`):
     - Install library native Linux untuk WeasyPrint (`libpango-1.0-0`, `libharfbuzz0b`, `libpangoft2-1.0-0`, `libpangocairo-1.0-0`, `libcairo2`, `libgdk-pixbuf-2.0-0`, `shared-mime-info`, `fonts-dejavu-core`) agar `test_report_renderer.py` dan `test_pdf_protector.py` ikut teruji penuh.
     - Setup `uv` (`astral-sh/setup-uv`), `uv sync --frozen --all-packages`.
     - Jalankan `uv run python scripts/check_quality.py --final`.
  2. **`postgres-semantics`** (`ubuntu-latest`, service `postgres:16-alpine` + healthcheck `pg_isready`):
     - Setup `uv`, `uv sync --frozen --all-packages`.
     - Jalankan `uv run pytest tests/models/test_postgres_semantics.py -v` terhadap container Postgres CI menggunakan kredensial dummy khusus CI.
  3. **`frontend-build`** (`ubuntu-latest`, Node `20`, `pnpm/action-setup`):
     - Jalankan `pnpm --dir apps/web install --frozen-lockfile`.
     - Jalankan `pnpm --dir apps/web run type-check` dan `pnpm --dir apps/web run build`.
- [ ] **5.2** Pastikan tidak ada satu pun kredensial nyata di dalam workflow (hanya placeholder environment test CI) dan validasi sintaks YAML-nya.

---

### Tahap 6 — Perbaikan `DOCS/BROWSER_TESTING_GUIDE.md` & Sinkronisasi Dokumentasi (Status Beta)
- [ ] **6.1** Perbaiki isi [`DOCS/BROWSER_TESTING_GUIDE.md`](BROWSER_TESTING_GUIDE.md) agar seluruh fitur baru terwakili akurat dan langkah pengujian sesuai kode aktual:
  - **Matriks RBAC & URL Publik:** Tambahkan rute ke-6 publik **`/verify/:code?`** (`Verify Report`) serta sebutkan tab ke-4 Superadmin **`Workspaces & Plans`** (`/app/admin?tab=workspaces`).
  - **Skenario 1 (`/contact` & `/verify`):**
    - Perbarui `/contact` agar menjelaskan alur **Enterprise Inquiry** (`> 50 Assets` atau pilihan Enterprise) yang tersimpan ke database & mengirim notifikasi email ke `sales@vulnflow.local` di Mailpit (`http://localhost:8025`).
    - Tambahkan sub-langkah verifikasi `/verify/:code` menggunakan kode dari footer/cover PDF Free tier.
  - **Skenario 2 (`/app/projects`):** Tambahkan pengisian opsional **`Tech Stack`** (`backend_framework`, `frontend_framework`, `database`, `runtime`, `cloud_provider`) dan pengaruhnya terhadap saran kode AI.
  - **Skenario 3 (`/app/ai-review` & `/app/theme`):**
    - Jelaskan alur job async Celery (`ai_worker` + status polling + cache prompt) saat menekan `Generate Draft`.
    - Jelaskan kelengkapan struktur PDF profesional (Cover, Executive Posture, Daftar Isi, Metodologi, Temuan, dan QR Verification).
    - Pada PDF **Free tier**, pastikan tester menguji ketahanan PDF hasil **rasterize** (teks/watermark tidak bisa diseleksi atau dihapus mudah) dan memindai/menyalin kode verifikasi `VF-XXXX-XXXX-XXXX` ke `/verify/<CODE>`.
  - **Skenario 4 (`/app/billing`):** Hapus catatan lama tentang `403 Access denied` Midtrans Sandbox; perbarui sesuai perbaikan `order_id` 47 karakter (`Upgrade to Pro` membuka Midtrans Snap Sandbox Checkout dan dapat di-sync lewat `Sync payment status`).
  - **Skenario 6 (`/app/admin`):** Tambahkan panduan pengujian tab ke-4 **`Workspaces & Plans`** (`/app/admin?tab=workspaces`), termasuk meninjau Enterprise Inquiry dan melakukan override paket/kuota workspace (`PRO`/`ENTERPRISE`).
- [ ] **6.2** Perbarui [`DOCS/QA_SIGN_OFF.md`](QA_SIGN_OFF.md):
  - Ubah seluruh link lokal `file:///c:/Users/.../IPPL/DOCS/...` menjadi tautan relatif repositori (`SRS.md`, `SDD.md`, `EDGE_CASES_AND_RESILIENCE.md`, `PLAN.md`, `AUDIT_FINDINGS.md`).
  - Perbarui angka verifikasi sesuai hasil aktual Tahap 3 (jumlah file `mypy --strict`, total test, persentase coverage, `0` CVE `pip-audit`, dan ukuran bundle Vite).
  - Ubah status dokumen menjadi **Beta Verification Snapshot (`v1.0.0-beta — Pending Final User Validation`)** agar tidak mengklaim rilis GA `v1.0.0` sebelum validasi Anda selesai.
- [ ] **6.3** Perbarui [`DOCS/PROJECT_CONTEXT.md`](PROJECT_CONTEXT.md) dan [`README.md`](../README.md):
  - Catat modul baru (`enterprise_inquiry.py`, `ollama_adapter.py`, `pdf_protector.py`, `ai_worker.py`, `VerifyReport.vue`, `docker-compose.prod.yml`, `.github/workflows/ci.yml`), Alembic head `b2c3d4e5f602`, serta cantumkan status rilis saat ini sebagai **`v1.0.0-beta`**.

---

### Tahap 7 — Reset Bersih Database & Object Storage Lokal
- [ ] **7.1** Hapus volume data uji lama (PostgreSQL, Redis, MinIO) dan nyalakan ulang stack dev yang bersih:
  ```powershell
  docker compose down -v
  docker compose up -d --build
  ```
- [ ] **7.2** Tunggu container sehat, pastikan Alembic menerapkan migrasi hingga `b2c3d4e5f602 (head)` via [`entrypoint.py`](../apps/api/entrypoint.py), lalu jalankan seeder default agar hanya tersedia akun Superadmin & template workspace awal:
  ```powershell
  docker compose exec -T api alembic -c apps/api/alembic.ini current
  docker compose exec -T api python -c "from app.core.database import make_engine, make_session_factory, get_database_url; from app.core.seeder import seed_defaults; s = make_session_factory(make_engine(get_database_url()))(); seed_defaults(s)"
  ```
- [ ] **7.3** Verifikasi database bersih & healthcheck:
  - `GET http://127.0.0.1:8000/health` → `200 {"status":"ok"}`.
  - Cek jumlah user pada tabel `users` hanya `1` (`admin@vulnflow.local`) dan tabel `findings` / `projects` / `reports` / `enterprise_inquiries` kosong (`0` baris).

---

### Tahap 8 — Audit Keamanan Pra-Commit & Commit Lokal Terstruktur (`main`, Tanpa Push)
- [ ] **8.1** Periksa `git status --short` dan `git diff --name-only`:
  - Pastikan **tidak ada** `.env`, private key (`*.pem`, `*.key`), file scan `*.jsonl`/`*.xml`, atau catatan scratch (`eval_*.md`, `antislop.md`) yang ter-stage.
  - Pastikan `DOCS/BETA_RELEASE_PLAN.md` sudah masuk rencana atau ter-commit sesuai kebutuhan dokumentasi.
- [ ] **8.2** Bagi seluruh perubahan ke dalam **6 commit lokal terstruktur** di branch `main`:
  1. `fix(billing,deps): enforce 50-char Midtrans order_id and pin transitive CVE fixes`  
     *(Cakupan: `apps/api/app/routers/billing.py`, `tests/api/test_billing_router.py`, `pyproject.toml`, `uv.lock`)*
  2. `feat(api,contracts): add enterprise inquiries, async AI worker, Ollama adapter, and PDF protection`  
     *(Cakupan: `packages/contracts/`, `apps/api/app/`, `apps/api/migrations/`, `apps/api/pyproject.toml`, dan `tests/` terkait)*
  3. `feat(web): add public report verification, tech-stack context, and enterprise admin flows`  
     *(Cakupan: seluruh perubahan `apps/web/src/`, `apps/web/vite.config.ts`)*
  4. `chore(infra): sync env defaults, worker config, and Nginx production Docker overlay`  
     *(Cakupan: `.env.example`, `docker-compose.yml`, `docker-compose.prod.yml`, `apps/web/Dockerfile`, `apps/web/nginx.conf`, `apps/web/.dockerignore`)*
  5. `ci: add GitHub Actions workflow for backend quality gates, Postgres semantics, and web build`  
     *(Cakupan: `.github/workflows/ci.yml`)*
  6. `docs: update browser testing guide, beta QA status, README, and project context`  
     *(Cakupan: `README.md`, `DOCS/BROWSER_TESTING_GUIDE.md`, `DOCS/QA_SIGN_OFF.md`, `DOCS/PROJECT_CONTEXT.md`, `DOCS/BETA_RELEASE_PLAN.md`)*
- [ ] **8.3** Verifikasi akhir Git lokal:
  - `git status --short` kosong (*clean working tree*).
  - `git log -n 8 --oneline` menampilkan urutan commit yang jelas.
  - **DILARANG** menjalankan `git push` dan **DILARANG** membuat tag `v1.0.0` pada tahap ini.

---

## 3. Checklist Validasi Manual Pemilik Proyek (Menuju `v1.0.0` GA)

Setelah Tahap 1–8 selesai dikerjakan dan status repo berada di **`v1.0.0-beta`** lokal:

1. **Uji Ulang Browser End-to-End Menggunakan [`DOCS/BROWSER_TESTING_GUIDE.md`](BROWSER_TESTING_GUIDE.md):**
   - Jalankan `pnpm --dir apps/web run dev` (atau uji mode production `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build` di `http://localhost:8080`).
   - Pastikan seluruh alur **Public** (`/`, `/contact` Enterprise Inquiry, `/verify/:code`), **Manager/Pentester/Viewer**, **Midtrans Sandbox Checkout**, **PDF Free Rasterize + QR Verify**, dan **Superadmin (`Workspaces & Plans`)** berjalan sesuai ekspektasi Anda.
2. **Tinjau Riwayat Commit Lokal:**
   - Periksa `git log -n 16 --stat` sebelum mempublikasikan ke GitHub.
3. **Promosi dari Beta ke `v1.0.0` (Hanya Dilakukan Anda Setelah Lolos Cek):**
   - Jika seluruh poin validasi sudah puas, baru perbarui label status `Beta` → `v1.0.0` bila perlu, lalu lakukan:
     ```powershell
     git push origin main
     ```
     *(Opsional saat benar-benar siap rilis resmi: buat tag `v1.0.0` dan push tag tersebut ke GitHub.)*

---

## 4. Risiko, Ketergantungan & Hal yang Harus Diwaspadai

| Area | Ketergantungan / Risiko | Mitigasi |
|:---|:---|:---|
| **Migrasi Alembic (`a1b2c3d4e501`, `b2c3d4e5f602`)** | Jika ada perbedaan kecil antara model SQLAlchemy terbaru dan skrip migrasi, DB fresh akan drift dari ORM. | Wajib jalankan `test_postgres_semantics.py` terhadap DB baru `vulnflow_test` di Tahap 3 **sebelum** reset bersih & commit. |
| **Worker Dependencies (`uv.lock`)** | `pypdfium2`, `pikepdf`, `pyhanko`, `segno` hanya masuk container setelah `docker compose up -d --build`. | Wajib rebuild image `api` & `worker` pada Tahap 2 dan uji PDF di dalam container `api` pada Tahap 3. |
| **`APP_BASE_URL` & `CORS_ALLOWED_ORIGINS`** | Mode dev berjalan di `:5173`, sedangkan mode Nginx overlay di `:8080`. Jika tidak di-override di `docker-compose.prod.yml`, link QR & CORS akan menunjuk `:5173`. | Pisahkan override environment di `docker-compose.prod.yml` untuk port `:8080` sementara default `.env.example` tetap `:5173`. |
| **Perlindungan Secret `.env`** | File `.env` menyimpan live key (`GEMINI_API_KEY`, `MIDTRANS_SERVER_KEY`, JWT/encryption key). | Verifikasi `git status --short` & `git diff --cached --name-only` sebelum setiap commit; jangan pernah mencetak nilai `.env`. |
