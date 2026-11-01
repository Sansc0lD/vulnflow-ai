# MASTER TRACKING PLAN & CODE QUALITY ASSURANCE

## Platform SaaS VulnFlow AI (Spec-Driven Development)

**Dokumen Acuan:** [SRS v3.5.0](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/SRS.md) | [SDD v1.6.0](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/SDD.md) | [Edge Cases & Resilience](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/EDGE_CASES_AND_RESILIENCE.md)  
**Metodologi:** **Spec-Driven Development (Contract-First / API-First)**  
**Status Proyek:** **FASE 4 Selesai & Seluruh Temuan Audit Selesai Diperbaiki $\rightarrow$ Siap Lanjut FASE 5 (CLI Agent)**  
**Terakhir Diperbarui:** 25 Oktober 2026

---

## 1. Indikator Kemajuan Proyek (*Overall Progress Tracker*)

```text
[████████████████████████████████████████████████████░░░░░] 87.5% (Dokumen + FASE 0-4 Selesai)
- Spesifikasi Kebutuhan (SRS v3.5.0)           : [x] SELESAI (100%)
- Desain Arsitektur Sistem (SDD v1.6.0)        : [x] SELESAI (100%)
- Matriks Kasus Batas & Ketahanan (EC-01..18) : [x] SELESAI (100%)
- Fase 0: Monorepo Scaffolding & Environment   : [x] SELESAI (100%, 6/6 sub-tugas)
- Fase 1: Pydantic V2 Shared Contracts         : [x] SELESAI (100%, 35 unit test, coverage 94.3%)
- Fase 2: Database Layer (The Lean 11 Tables)  : [x] SELESAI (100%, 6/6 sub-tugas, 59 unit test, coverage 97.3%)
- Fase 3: Domain Core & Security Engines       : [x] SELESAI (100%, 6/6 sub-tugas, 120 test case, coverage 96.7%)
- Fase 4: FastAPI Routers & Celery Worker      : [x] SELESAI (100%, 330 test, 91.4% cov) — SELURUH TEMUAN AUDIT (2 CRITICAL + 16 HIGH + 25 MED + 24 LOW) TELAH DIPERBAIKI & DIVERIFIKASI (lihat AUDIT_FINDINGS.md §5)
- Fase 5: CLI Agent Lintas Platform            : [ ] BELUM DIMULAI (0%)
- Fase 6: Web Dashboard SPA (Vue 3 + shadcn-vue): [ ] BELUM DIMULAI (0%)
- Fase 7: QA & Resilience Test Suite           : [ ] BELUM DIMULAI (0%)
```

---

## 2. Arsitektur Jaminan Kualitas Kode (*Code Quality Assurance Stack*)

Untuk memastikan kode bersih, aman dari kerentanan (*secure by design*), bebas *technical debt*, dan memiliki performa tinggi, proyek menerapkan standar mutu berjenjang (*Quality Gates*):

```
                               PIRAMIDA JAMINAN MUTU KODE
                                 ┌──────────────────┐
                                 │   E2E & Kasus    │  18 Skenario Edge Cases
                                 │  Batas (Pytest)  │  (tests/test_resilience)
                                 ├──────────────────┤
                                 │ Uji Integrasi &  │  FastAPI TestClient
                                 │   Kontrak API    │  (Coverage >= 85%)
                                 ├──────────────────┤
                                 │ Static Security  │  Bandit (SAST) &
                                 │   Scan (SAST)    │  pip-audit (CVE deps)
                                 ├──────────────────┤
                                 │ Strict Typecheck │  Mypy --strict
                                 │   (Zero Any)     │  (Pydantic V2 strict)
                                 ├──────────────────┤
                                 │ Lint & Format    │  Ruff (Fast Linter)
                                 │  (Otomatis)      │  Black/Flake8/isort rule
                                 └──────────────────┘
```

### 2.1 Tooling Mutu Backend & CLI (Python 3.12+)

| Perkakas           | Kategori              | Peran & Standar Konfigurasi                                                                                                                                         | Toleransi Galat                   |
|:------------------ |:--------------------- |:------------------------------------------------------------------------------------------------------------------------------------------------------------------- |:---------------------------------:|
| **`Ruff`**         | *Linter & Formatter*  | Menggantikan Black, Flake8, isort, dan pydocstyle. Menegakkan gaya kode PEP 8, import sorting, dan deteksi anti-pattern dengan kecepatan ultra-tinggi (Rust-based). | **0 Error (Zero-tolerance)**      |
| **`Mypy`**         | *Static Type Checker* | Menegakkan pengetikan statis ketat (`--strict`). Melarang penggunaan `Any` implisit dan memastikan konsistensi tipe antara Pydantic V2 dan endpoint FastAPI.        | **0 Error (Strict Mode)**         |
| **`Bandit`**       | *Security SAST*       | Memindai celah keamanan pada kode Python: penggunaan fungsi berbahaya (`eval`, `exec`), SQL injection mentah, hardcoded secret, atau kriptografi lemah.             | **0 High/Medium Vulnerabilities** |
| **`pip-audit`**    | *Dependency Audit*    | Memeriksa seluruh dependensi pustaka di `pyproject.toml` terhadap basis data kerentanan CVE global (PyPA Advisory Database).                                        | **0 Known CVEs**                  |
| **`Pytest + Cov`** | *Testing & Coverage*  | Menjalankan unit test, integrasi, dan skenario edge cases dengan target cakupan kode minimal **85%**.                                                               | **$\ge 85\%$ Code Coverage**      |

### 2.2 Tooling Mutu Frontend Web (Vue 3 + TypeScript)

| Perkakas               | Kategori         | Peran & Standar Konfigurasi                                                                 | Toleransi Galat    |
|:---------------------- |:---------------- |:------------------------------------------------------------------------------------------- |:------------------:|
| **`ESLint`**           | *Linter JS/TS/Vue* | Menegakkan aturan `typescript-eslint` dan `eslint-plugin-vue` (`vue/setup-compiler-macros`, aturan Composition API).  | **0 Error**        |
| **`Prettier`**         | *Code Formatter* | Format konsisten (termasuk berkas `.vue`) + `prettier-plugin-tailwindcss` untuk sorting class Tailwind CSS otomatis. | **100% Formatted** |
| **`vue-tsc`**          | *Type Checking*  | `vue-tsc --noEmit` dengan `strict: true` untuk menjamin tidak ada `any` yang lolos, termasuk tipe di dalam `<script setup lang="ts">`. | **0 Type Errors**  |

### 2.3 Skrip Pemeriksa Kualitas Otomatis Mandiri (`scripts/check_quality.py`)

Proyek akan menyertakan skrip satu pintu yang dapat dijalankan pengembang di terminal lokal sebelum melakukan commit:

```bash
# Perintah cepat satu langkah untuk memvalidasi seluruh mutu kode
$ python scripts/check_quality.py
[1/5] Menjalankan Ruff Formatter & Linter...        [✓ PASS]
[2/5] Menjalankan Mypy Strict Type Check...         [✓ PASS]
[3/5] Menjalankan Bandit Security SAST...           [✓ PASS]
[4/5] Menjalankan Pytest & Evaluasi Coverage...     [✓ PASS] (Coverage: 91.4%)
[5/5] Memeriksa Kerentanan Dependensi (Audit)...    [✓ PASS] (0 CVEs)

[SUCCESS] Seluruh Quality Gates Lolos! Kode siap di-commit.
```

---

## 3. Rencana Kerja Detail per Fase (Tracking Checklist)

---

### FASE 0: Inisialisasi Monorepo & Lingkungan Pengembangan

> **Tujuan:** Menyiapkan struktur direktori monorepo, isolasi dependensi via `uv`, dan container pendukung lokal.

- [x] **0.1** Inisialisasi Git repository lokal (`git init`).
- [x] **0.2** Konfigurasi workspace root `pyproject.toml` (mendukung `apps/api`, `apps/cli`, `packages/contracts` via `uv` workspace; diverifikasi dengan `uv sync --all-packages` — seluruh 3 member & dependensinya resolve tanpa konflik).
- [x] **0.3** Pembuatan struktur direktori:
  - [x] `packages/contracts/`
  - [x] `apps/api/`
  - [x] `apps/cli/`
  - [x] `apps/web/`
  - [x] `scripts/`
  - [x] `tests/` (root-level, bukan di dalam masing-masing app/package — lihat `tests/contracts/`, `tests/test_resilience/` yang dirujuk FASE 1.7 & 7.2)
- [x] **0.4** Konfigurasi `docker-compose.yml` untuk infrastruktur lokal (kredensial via `.env`, lihat `.env.example`; tidak ada password hardcoded di file yang di-commit):
  - [x] PostgreSQL 16 (Port 5432, credential aman)
  - [x] Redis 7.2 (Port 6379)
  - [x] MinIO Object Storage (Port 9000 & Web Console 9001)
- [x] **0.5** Konfigurasi linter & type checker di `pyproject.toml` (`[tool.ruff]`, `[tool.mypy]`, `[tool.pytest]`, `[tool.bandit]`, `[tool.coverage]`).
- [x] **0.6** Pembuatan skrip `scripts/check_quality.py` untuk otomatisasi audit mutu — diverifikasi jalan end-to-end (mode proporsional FASE 0-6 dan mode `--final` FASE 7.3 keduanya teruji).

---

### FASE 1: Pembangkitan Data Contracts Bersama (`packages/contracts`)

> **Tujuan:** Mengonversi spesifikasi JSON Schema Bab 2.6.1 SDD menjadi model tipe data Pydantic V2 tanpa deviasi.

- [x] **1.1** Implementasi `packages/contracts/vulnflow_contracts/error_envelope.py`:
  - [x] Model `StandardErrorEnvelope` (RFC 9110: `status`, `code`, `message`, `details`, `timestamp`).
  - [x] Enum `ErrorCode` (`AUTHENTICATION_FAILED`, `QUOTA_EXHAUSTED`, `BATCH_LIMIT_EXCEEDED`, dll.).
- [x] **1.2** Implementasi `packages/contracts/vulnflow_contracts/finding_schemas.py`:
  - [x] Model `ProofOfConceptSchema` (`raw_evidence`, `reproduction_steps`, `attachment_urls`).
  - [x] Model `UnifiedVulnerabilityFinding` (CVSS v3.1/v4.0, CWE regex `^(CWE-[0-9]+|UNKNOWN)$` per SDD §2.6.1.1, nullable `target_port`).
  - [x] Model `BatchIngestRequest` & `BatchIngestResponse`.
  - [x] Model `ManualFindingRequest` & `ManualFindingResponse` (FR-INGEST-004 / UC-08).
- [x] **1.3** Implementasi `packages/contracts/vulnflow_contracts/auth_schemas.py`:
  - [x] Model `RegisterRequest` (validasi kata sandi min. 8 karakter, wajib huruf besar/kecil, angka & simbol).
  - [x] Model `LoginRequest`, `TokenResponse`, dan `UserDTO`.
- [x] **1.4** Implementasi `packages/contracts/vulnflow_contracts/ai_schemas.py`:
  - [x] Model `AINarrativeRequest` & `AINarrativeResponse` (format output JSON manajerial).
- [x] **1.5** Implementasi `packages/contracts/vulnflow_contracts/report_schemas.py`:
  - [x] Model `CompilePDFRequest` (opsi tema, white-labeling, id temuan terpilih).
  - [x] Model `ReportJobStatusResponse` & `ReportDownloadResponse`.
- [x] **1.6** Implementasi `packages/contracts/vulnflow_contracts/billing_schemas.py`:
  - [x] Model `MidtransCheckoutRequest` & `MidtransCheckoutResponse` (`snap_token`).
  - [x] Model `MidtransWebhookPayload` (validasi format signature SHA-512: panjang 128 hex char; verifikasi kriptografis penuh terhadap ServerKey tetap di domain service FASE 4).
- [x] **1.7** Pengujian Unit Kontrak:
  - [x] Test serialisasi & deserialisasi model Pydantic V2 (`tests/contracts/test_schemas.py`) — 35 test, memakai contoh JSON asli SDD §2.6.1/§2.6.3 + kasus validasi gagal (CWE malformed, port di luar rentang, password lemah, gross_amount Midtrans belum ternormalisasi).
  - [x] Validasi kesesuaian JSON Schema terhadap Bab 2.6.1 SDD — diverifikasi lolos `check_quality.py` (ruff, mypy --strict, bandit, pytest 94.3% coverage, pip-audit).

---

### FASE 2: Arsitektur Basis Data & Migrasi Relasional (*The Lean 11 Tables*)

> **Tujuan:** Mengimplementasikan 11 model relasional SQLAlchemy 2.0 (Sync mode) dan inisialisasi Alembic, mengacu penuh pada **SDD Bab 2.4.2 (Kamus Data Teknis) tanpa deviasi** — daftar kolom pada tiap tabel di bawah ini hanya contoh ilustratif/kolom yang paling krusial, bukan spesifikasi kolom yang lengkap; implementasi wajib menyalin skema penuh dari Kamus Data SDD.

- [x] **2.1** Konfigurasi koneksi basis data & session factory di `apps/api/app/core/database.py`.
- [x] **2.2** Inisialisasi Alembic migrations (`apps/api/migrations/`).
- [x] **2.3** Implementasi 11 Tabel SQLAlchemy Model (`apps/api/app/models/`):
  - [x] `User` (`users` - UUID PK, email index, password_hash Argon2id, token_version).
  - [x] `Workspace` (`workspaces` - custom_logo_url, brand colors, confidentiality_text).
  - [x] `WorkspaceMember` (`workspace_members` - workspace_id FK, user_id FK, role ENUM).
  - [x] `Subscription` (`subscriptions` - tier, reports counter, Midtrans fields).
  - [x] `APIKey` (`api_keys` - key_hash SHA-256, label, is_active).
  - [x] `Project` (`projects` - target_scope, roe dates, lead_pentester_id FK).
  - [x] `Finding` (`findings` - dedup_hash, cvss metrics, nullable target_port, version int).
  - [x] `ProofOfConcept` (`proofs_of_concept` - AES-256-GCM encrypted_raw_evidence, iv_nonce, auth_tag, **key_version** [wajib, dasar rotasi kunci master — SDD §2.4.3]).
  - [x] `AINarrative` (`ai_narratives` - project_id FK, tokens_consumed, is_fallback).
  - [x] `Report` (`reports` - project_id FK, storage_path, watermark_applied).
  - [x] `AuditLog` (`audit_logs` - partition by range created_at monthly; composite PK `(id, created_at)` wajib secara teknis di PostgreSQL untuk kolom partition key, plus partisi `DEFAULT` agar tabel langsung bisa menerima INSERT — partisi bulanan otomatis didelegasikan ke scheduled job di fase berikutnya).
- [x] **2.4** Helper Kriptografi Enkripsi Kolom At-Rest:
  - [x] Modul `apps/api/app/core/crypto.py` (AES-256-GCM AEAD enkripsi/dekripsi bukti PoC).
- [x] **2.5** Eksekusi migrasi awal:
  - [x] `alembic revision --autogenerate -m "create_lean_11_tables"`
  - [x] `alembic upgrade head`
- [x] **2.6** Pembuatan seeder data default (`apps/api/app/core/seeder.py`):
  - [x] Seed akun admin awal, template paket langganan Free & Pro.

**Bukti Verifikasi (22 Oktober 2026):** 59 unit test (`tests/core/`, `tests/models/`), coverage 97.3%, seluruh 11 tabel + partisi `audit_logs_default` dikonfirmasi di PostgreSQL 16 lokal (`docker compose up postgres` + `alembic upgrade head`); seeder dijalankan dua kali berturut-turut terhadap database nyata untuk memverifikasi idempotensi (1 admin, 2 workspace template FREE/PRO dengan kuota 3/30 — tidak terduplikasi). Model menggunakan tipe kolom cross-dialect (`Uuid`, `JSON().with_variant(JSONB, "postgresql")`, `DateTime(timezone=True)`) agar unit test berjalan di SQLite tanpa Docker, sementara DDL PostgreSQL tetap sesuai SDD §2.4.2 (UUID/JSONB/TIMESTAMPTZ/BYTEA asli). `uv run python scripts/check_quality.py` lolos (ruff, mypy --strict, bandit, pip-audit nol temuan).

**Review Pasca-Implementasi (22 Oktober 2026, sebelum FASE 3):** Manual code review menemukan 1 bug nyata (bukan drift dokumen): `findings.dedup_hash` memiliki `index=True` pada kolom DAN `UniqueConstraint` terpisah di `__table_args__` — dua konstruksi SQLAlchemy yang independen sehingga menghasilkan **dua index btree redundan** pada kolom yang sama (`ix_findings_dedup_hash` + `uq_finding_dedup`), terverifikasi langsung di PostgreSQL via `\d findings`. Pola `unique=True` + `index=True` langsung pada kolom (dipakai di `users.email`, `subscriptions.workspace_id`, `proofs_of_concept.finding_id`) sudah benar menyatu jadi satu index — hanya `findings.dedup_hash` yang memakai pola berbeda dan luput. Diperbaiki: `index=True` dihapus dari kolom, `UniqueConstraint` tetap menyediakan index untuk lookup. Migrasi awal diedit langsung (belum pernah di-commit/dibagikan) lalu `alembic downgrade base && alembic upgrade head` dijalankan ulang; 59 test tetap lolos, seeder diverifikasi ulang idempoten terhadap database yang di-migrasi ulang.

**Review Pasca-Implementasi Kedua (25 Oktober 2026, setelah FASE 4):** Review baris-per-baris atas 12 model + `migrations/env.py` + migrasi awal, dengan setiap temuan diverifikasi langsung terhadap PostgreSQL 16 yang berjalan (bukan pattern-matching). Ditemukan 4 cacat HIGH, 4 MEDIUM, 3 LOW; semuanya diperbaiki oleh migrasi `d4a7f1c93b28_harden_lean_11_schema`:

1. **`audit_logs.workspace_id` memakai `ON DELETE CASCADE`** (terverifikasi: `confdeltype='c'`), padahal SRS UC-04 E2 langkah 2 & UC-19 E1 mewajibkan baris audit **dipertahankan** setelah workspace di-purge ("tidak di-cascade-delete"). Job purge akan menghapus seluruh jejak audit workspace tersebut — termasuk entri `WORKSPACE_PURGED` yang baru ditulis — lewat trigger integritas referensial yang berjalan dengan hak pemilik tabel, sehingga `REVOKE DELETE` di SDD §2.4.4 tidak melindunginya. FK dihapus; kolom kini menyimpan `workspace_id` sebagai referensi historis menggantung, persis seperti bunyi SRS.
2. **`audit_logs` hanya punya partisi `DEFAULT`.** Terbukti di PostgreSQL 16: begitu ada satu baris di partisi default, `CREATE TABLE ... PARTITION OF ... FOR VALUES` gagal dengan `updated partition constraint for default partition would be violated by some row` — artinya partisi bulanan (SDD §2.4.4) **tidak akan pernah bisa** dibuat oleh scheduled job, dan semua kueri audit memindai satu partisi yang terus membesar (melanggar target <200 ms). Ditambahkan partisi bulan berjalan + bulan depan, serta fungsi `create_audit_log_partition(date)` yang memindahkan baris keluar dari partisi default sebelum attach sehingga idempoten dan aman dipanggil kapan pun.
3. **`findings.version` tidak terdaftar sebagai `version_id_col`**, sehingga EC-11 hanya berupa perbandingan di Python (TOCTOU): di READ COMMITTED dua request triase sama-sama membaca version=1, sama-sama lolos, dan UPDATE kedua menimpa yang pertama (lost update, keduanya menerima HTTP 200). Sekarang `__mapper_args__` membuat UPDATE membawa `WHERE version = :old_version` dan `StaleDataError` dipetakan ke `409 Conflict`.
4. **Index unik `users.email` bersifat case-sensitive** (terverifikasi: `'Alice@corp.com' = 'alice@corp.com'` → `f`), sehingga satu mailbox bisa punya dua akun dan login bergantung pada kapitalisasi yang diketik. Ditambahkan index fungsional unik `uq_users_email_lower` + tipe kontrak `NormalizedEmail` di lapisan Pydantic.
5. **`proofs_of_concept.reproduction_steps` dianotasi `dict[str, Any]`** padahal kontrak dan kedua jalur ingesti menulis array (`list[str]`); JSONB menerima keduanya sehingga tidak ada error tulis, tapi tipe yang dideklarasikan berlawanan dengan data tersimpan dan `mypy --strict` tidak bisa menangkapnya (konstruktor SQLAlchemy `**kw: Any`).
6. **`findings` tidak punya `created_at`** padahal `ManualFindingResponse.created_at` adalah field wajib — API mengarang timestamp yang tidak pernah disimpan, dan UC-11 retest tidak punya tanggal first-seen.
7. **Kebijakan `ondelete` pada `users.id` tidak konsisten** sehingga jaminan tingkat-basis-data EC-03 mustahil: `workspace_members.user_id` CASCADE membuat DELETE user sukses dan menelantarkan workspace tanpa anggota (tetap memegang proyek/temuan/PoC), sementara tiga FK lain default NO ACTION menghasilkan `IntegrityError` → HTTP 500, bukan `409`. Kini `workspace_members.user_id` NO ACTION (database menolak, sesuai SDD §2.7.1) dan `projects.lead_pentester_id` `SET NULL`.
8. **Dialek SQLite membuang `tzinfo` secara senyap** pada `DateTime(timezone=True)` (terverifikasi: nilai aware kembali naive), jadi logika perbandingan waktu EC-05 divalidasi dengan semantik yang salah — dan migrasi sama sekali tidak pernah dieksekusi oleh test apa pun. Ditambahkan lane `tests/models/test_postgres_semantics.py` (opt-in via `TEST_DATABASE_URL`) yang menjalankan `alembic upgrade head` ke PostgreSQL nyata lalu memverifikasi tz-awareness, retensi audit, provisioning partisi, EC-03, keunikan email, dan **nol drift model↔migrasi** via `compare_metadata`.
9. **`alembic revision --autogenerate` mengusulkan `op.drop_table('audit_logs_default')`** (terverifikasi dengan menjalankannya) karena partisi direfleksikan sebagai tabel biasa dan tidak ada di `Base.metadata` — satu `--autogenerate` yang dipercaya begitu saja akan menghapus jejak audit, dan downgrade hasil generate membuatnya kembali sebagai tabel inherit biasa, bukan partisi, jadi tidak bisa dipulihkan. Diperbaiki via `app/core/migration_filters.py` yang menyaring partisi berdasarkan `pg_class.relispartition`; `alembic check` kini bersih.
10. **Tanpa `MetaData(naming_convention=...)`** seluruh FK dinamai server, sehingga Alembic merender `op.drop_constraint(None, ...)` + warning (migrasi yang gagal saat dijalankan). Konvensi `ix`/`uq`/`fk` ditambahkan dan 12 FK dinormalkan namanya. Catatan penting: Alembic menerapkan konvensi `target_metadata` pada `op.create_table`, jadi nama FK berbeda tergantung **kapan** database dibangun — migrasi ini karena itu mencari FK berdasarkan (tabel, kolom, tabel referensi), bukan berdasarkan nama, agar benar untuk database lama maupun baru.
11. **`subscriptions.midtrans_order_id` tidak unik** padahal webhook me-resolve-nya dengan `.one_or_none()` (`MultipleResultsFound` → HTTP 500 di endpoint tanpa autentikasi); kini unik, sesuai deskripsi SDD §2.4.2 #4 ("kode referensi order unik").
12. **`workspaces.is_deleted` tidak dibaca di mana pun**, sehingga workspace yang sudah soft-delete tetap bisa dibaca & ditulis selama 30 hari retensi. Ditambahkan `workspace_is_active()` dan dipasang di `require_workspace_role` serta jalur autentikasi API key.

**Bukti Verifikasi Review Kedua:** `alembic upgrade head` → `downgrade base` → `upgrade head` bersih di database kosong; migrasi juga diterapkan ke database dev nyata (jalur nama FK lama) dengan 12 FK ternormalkan, partisi `audit_logs_y2026m10`/`y2026m11` terbentuk, dan data utuh; `alembic check` tanpa drift; 11 test PostgreSQL + 7 test SQLite baru lolos (total 277 passed, 12 skipped); ruff, `mypy --strict`, bandit nol temuan; seeder diverifikasi ulang idempoten. Catatan: `downgrade` **menolak** berjalan jika sudah ada baris audit yang melampaui workspace-nya, karena PostgreSQL tidak mengizinkan FK `NOT VALID` pada tabel terpartisi — menolak dengan pesan jelas dipilih ketimbang menghapus bukti kepatuhan secara senyap.

---

### FASE 3: Layanan Domain & Engine Inti (*Application Logic*)

> **Tujuan:** Membangun domain logic murni dan modul keamanan yang berdiri sendiri (*Pure Business Logic*).

- [x] **3.1** `DeduplicationService` (`apps/api/app/domain/deduplication.py`):
  - [x] Formula hash deterministik: $\text{SHA256}(\text{project\_id} + \text{cwe} + \text{host} + \text{port} + \text{path})$.
  - [x] Uji unit ketepatan hash pada berbagai variasi endpoint (EC-08).
- [x] **3.2** `CVSSCalculator` (`apps/api/app/domain/cvss.py`):
  - [x] Parsing string vektor CVSS v3.1 (`AV:N/AC:L/...`).
  - [x] Perhitungan skor dasar metrik matematis FIRST CVSS (0.0 s.d. 10.0).
- [x] **3.3** `ScopeEnforcer` (`apps/api/app/domain/scope.py`):
  - [x] Normalisasi URL/FQDN & pencocokan CIDR (`ipaddress`).
  - [x] Predikat `is_target_in_scope()` (nested-subdomain-aware, EC-04) — penandaan `is_quarantined = true` pada baris `findings` dilakukan oleh `IngestRouter` di FASE 4 (UC-07d), modul ini hanya logika murni penentuan in/out-of-scope.
- [x] **3.4** `PromptSanitizationService` (`apps/api/app/domain/sanitizer.py`):
  - [x] Pelucutan alamat IP privat, port, URL mentah, dan bukti PoC (UC-11a) — via whitelist kolom ketat (`whitelist_finding_metadata`) + `sanitize_text` untuk teks bebas.
  - [x] Pembersihan karakter kontrol pencegah *Indirect Prompt Injection* (EC-13).
- [x] **3.5** `DeterministicFallbackEngine` (`apps/api/app/domain/fallback.py`):
  - [x] Berkas data `apps/api/app/data/cwe_catalog.json` (kurasi narasi remediasi CWE, termasuk entri `UNKNOWN` sebagai fallback default).
  - [x] Pemuatan in-memory dengan `lru_cache` (dibaca dari disk sekali, lookup dict $\mathcal{O}(1)$) (UC-11b / EC-14).
- [x] **3.6** `SafeURLFetcher` (`apps/api/app/services/safe_fetcher.py`):
  - [x] Custom fetcher WeasyPrint pencegah SSRF (Bab 2.5 SDD) — menggunakan properti `ipaddress` (`is_private/is_loopback/is_link_local/is_reserved/is_unspecified/is_multicast` + `ipv4_mapped`) alih-alih daftar CIDR manual, memperbaiki gap yang ditemukan audit FASE-2 (IPv4-mapped IPv6 seperti `::ffff:127.0.0.1`). `default_fetcher` di-inject (bukan impor langsung `weasyprint.default_url_fetcher`) agar modul ini testable tanpa dependensi WeasyPrint/network — pengkabelan nyata ke WeasyPrint adalah pekerjaan FASE 4.
  - [x] Blokir akses IP privat RFC 1918, cloud metadata 169.254.0.0/16, loopback, dan skema `file://` (terverifikasi via test parametrized, lihat Bukti Verifikasi).

**Bukti Verifikasi (22 Oktober 2026):** 99 unit test baru (120 test case setelah ekspansi parametrize) di `tests/domain/` dan `tests/services/`, total proyek 120 test case, coverage 96.7%. `calculate_base_score` diverifikasi terhadap 3 vektor CVSS v3.1 referensi (termasuk kalkulasi tangan untuk kasus *Scope Changed*, bukan sekadar membaca kode). `safe_url_fetcher` diverifikasi memblokir IPv4-mapped IPv6 loopback (`::ffff:127.0.0.1`) — persis gap yang diidentifikasi pada audit sebelum FASE 2. `uv run python scripts/check_quality.py` lolos (ruff, mypy --strict, bandit, pip-audit nol temuan).

**Review Pasca-Implementasi (22 Oktober 2026, sebelum FASE 4):** `/find-bugs` + `/systematic-debugging` menemukan 2 bug keamanan nyata di modul FASE 3 (dibuktikan empiris, bukan sekadar membaca kode):
1. **[DIPERBAIKI]** `sanitizer.py` `_HOSTNAME_PATTERN` memakai regex ber-*nested quantifier* (`(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}`) yang rentan *catastrophic/quadratic backtracking* — diukur 8-34 detik untuk payload 40 ribu karakter `"a."` berulang. Ini relevan langsung karena `sanitize_text` justru didesain memproses teks banner scanner yang berasal dari penyerang (model ancaman EC-13 sendiri). Diperbaiki dengan regex datar tanpa nesting (`[a-zA-Z0-9.-]+`, O(n)) + validasi bentuk-hostname di callback Python (`_looks_like_hostname`). Diverifikasi turun dari 34 detik menjadi <0.01 detik pada payload identik; ditambahkan 2 test regresi permanen (`test_sanitize_text_runs_in_linear_time_on_adversarial_dotted_input`, `..._on_mixed_adversarial_banner`) plus stress-test manual ke-3 regex lain di modul (semua O(n), aman).
2. **[DITUNDA KE FASE 4, didokumentasikan]** `safe_fetcher.py` memvalidasi hostname→IP sekali untuk cek anti-SSRF, lalu memanggil `default_fetcher(url, ...)` dengan URL asli (bukan IP yang sudah divalidasi) — `default_fetcher` akan me-resolve DNS lagi secara independen saat benar-benar melakukan fetch. Dibuktikan empiris: simulasi DNS rebinding (lookup pertama kembalikan IP publik, lolos validasi; lookup kedua saat fetch nyata kembalikan `127.0.0.1`) berhasil membypass guard sepenuhnya. Perbaikan root-cause (resolve-sekali + pin IP via `httpx` dengan `Host` header & SNI override, bukan monkeypatch `socket` global yang tidak aman untuk Celery worker konkuren) **sengaja ditunda ke FASE 4** karena baru di sana `default_fetcher` benar-benar dikabel ke WeasyPrint nyata — memperbaikinya sekarang berisiko membuat asumsi yang salah tentang API WeasyPrint yang sebenarnya.

---

### FASE 4: Implementasi REST API & Worker Asinkron (`apps/api`)

> **Tujuan:** Membangun endpoint web API FastAPI, middleware keamanan, dan background worker Celery/Redis.

- [x] **4.1** Middleware & Error Handling:
  - [x] Global Exception Handler yang membungkus seluruh galat HTTP ke dalam `StandardErrorEnvelope` (termasuk `RequestValidationError` → 422 dan `Exception` tak terduga → 500 tanpa membocorkan detail internal).
  - [x] CORS middleware & Security Headers (HSTS, CSP, X-Content-Type-Options, X-Frame-Options).
  - [x] **Kontrak baru ditambahkan**: `ErrorCode.CONFLICT` (HTTP 409) — SDD §2.6.1.7 hanya mendaftar 8 kode, tapi EC-03/EC-11 secara eksplisit membutuhkan `409 Conflict` dan tidak ada kode untuk itu sampai sekarang.
- [x] **4.2** `AuthRouter` (`apps/api/app/routers/auth.py`):
  - [x] `POST /api/v1/auth/register` (Registrasi akun + pembuatan workspace default + Subscription FREE; mendukung `invitation_token` EC-02 untuk join workspace yang mengundang).
  - [x] `POST /api/v1/auth/login` (Otentikasi Argon2id + JWT token issuance; mitigasi timing-attack user-enumeration via dummy-hash verify).
  - [x] Verifikasi `token_version` pada dependensi `get_current_user`.
- [x] **4.3** `WorkspaceRouter` & `ProjectRouter`:
  - [x] CRUD Workspace (create/update/invite-member/create-api-key), RBAC permissions guard (`MANAGER`, `PENTESTER`, `VIEWER` — SDD §2.4.2 Tabel 3).
  - [x] Inisialisasi Proyek Audit & validasi rentang tanggal ROE (EC-05, divalidasi di kontrak `ProjectCreateRequest`), assign lead pentester (UC-06a).
- [x] **4.4** `IngestRouter` (`apps/api/app/routers/ingest.py`):
  - [x] `POST /api/v1/workspaces/{w_id}/projects/{p_id}/findings/batch` (Verifikasi API Key via `X-VulnFlow-API-Key`, paywall check batas 50 temuan Free Tier `HTTP 413`) — mengkabel `ScopeEnforcer` (is_quarantined), `DeduplicationService` (dedup_hash), `CVSSCalculator` (fallback skor dari vector), dan `crypto.encrypt_poc` (FASE 3 → produksi, bukan lagi modul terisolasi).
  - [x] `POST /api/v1/workspaces/{w_id}/projects/{p_id}/findings/manual` (Entri manual CVSS via `CVSSCalculator`).
- [x] **4.5** `TriageRouter` (`apps/api/app/routers/triage.py`):
  - [x] `PATCH /api/v1/.../findings/{id}/status` dengan *Optimistic Locking* kolom `version` (`HTTP 409 CONFLICT`), mencatat `audit_logs` (IP klien asli, bukan placeholder).
  - [x] Auto-uncheck `is_curated_for_report` saat status diubah ke `FALSE_POSITIVE` (EC-12).
- [x] **4.6** `AIRouter` (`apps/api/app/routers/ai.py`):
  - [x] `AIGhostwriterService` (`app/domain/ai_ghostwriter.py`): orkestrasi `PromptSanitizationService` (whitelist metadata) → 3x exponential retry via `GeminiLLMAdapter` (`httpx` langsung ke REST API Gemini, bukan SDK resmi — menghindari dependensi baru, konsisten dengan pola proyek) → `DeterministicFallbackEngine` otomatis saat retry habis (EC-14).
  - [x] Diverifikasi: adapter hanya menerima 4 field whitelist (title/cwe_id/cvss_score/severity), tidak pernah target_host/PoC — Zero-PoC-to-AI dibuktikan lewat assertion langsung di test, bukan sekadar membaca kode.
- [x] **4.7** `ReportRouter` & Celery Worker (`apps/api/app/workers/report_worker.py`):
  - [x] `POST /api/v1/.../reports/compile-pdf` (`HTTP 202 Accepted` + Celery task via `compile_pdf_task.delay()`).
  - [x] *Distributed Lock* Redis 10 detik (`lock:report:{project_id}`, `app/core/redis_client.py`) cegah double-click — klik kedua mengembalikan `job_id` yang sama (EC-15).
  - [x] Worker WeasyPrint render HTML/CSS (`app/services/report_renderer.py`) + unggah S3/MinIO (`app/services/s3_storage.py`).
    - ✅ **Gap DNS-rebinding dari FASE 3 diperbaiki di sini** (bukan ditunda lagi): `safe_fetcher.py` ditulis ulang — bukan lagi validasi-lalu-delegasi ke `default_fetcher`, melainkan fetch mandiri yang connect langsung ke IP yang sudah divalidasi (satu resolusi DNS, tidak pernah dua), dengan `Host` header & `sni_hostname` extension `httpx` tetap memakai hostname asli. Diverifikasi via `httpx.MockTransport`: request yang benar-benar dikirim terbukti menyasar IP yang sudah divalidasi, bukan hasil resolusi ulang.
  - [x] Handler `compile_report` rollback kuota otomatis jika render crash (EC-16) — diverifikasi: crash render tidak membuat baris `Report`, tidak mengunggah ke S3, dan tidak menambah `reports_used_this_month`.
  - [x] `GET /api/v1/workspaces/{w_id}/reports/{report_id}/download` (Proxy regenerasi presigned URL segar `HTTP 307`) (EC-17).
  - ⚠️ **Keterbatasan lingkungan terdokumentasi**: WeasyPrint butuh pustaka native GTK3/Pango/Cairo yang tidak selalu terpasang di setiap mesin dev (hadir di target deployment Docker Linux sesuai `docker-compose.yml`/prasyarat SDD) — import di-lazy-kan, dan test render PDF nyata `skip` secara eksplisit (dengan alasan tercatat) jika pustaka native tidak tersedia, bukan dipalsukan lolos.
- [x] **4.8** `BillingRouter` (`apps/api/app/routers/billing.py`):
  - [x] `POST /api/v1/workspaces/{w_id}/billing/checkout` (Koneksi Midtrans Snap API via `MidtransAdapter`, `httpx` langsung — bukan SDK resmi).
  - [x] `POST /api/v1/billing/webhook/midtrans` (Validasi tanda tangan SHA-512 case-insensitive constant-time & idempotency check — diverifikasi webhook duplikat tidak merusak state) (EC-18).
  - ℹ️ Harga self-service hanya tersedia untuk tier PRO (Rp 750.000, sesuai contoh SDD §2.3.4); ENTERPRISE tidak dipasarkan dengan harga di dokumen manapun yang dibaca, sehingga checkout ENTERPRISE sengaja ditolak dengan `422` (sales-led, bukan self-service) alih-alih menebak angka.

**Bukti Verifikasi (24 Oktober 2026):** 271 test case total di seluruh proyek (naik dari 120 di akhir FASE 3 — 151 test baru FASE 4), coverage 94.4%. Seluruh 8 sub-fase dibangun murni TDD (merah→hijau per endpoint/modul), termasuk 2 kontrak baru yang ditemukan hilang saat implementasi dan ditambahkan dengan test (`ErrorCode.CONFLICT`, serta modul `workspace_schemas.py` lengkap untuk Workspace/Project/APIKey/Invite CRUD yang belum ada sejak FASE 1). `uv run python scripts/check_quality.py` lolos (ruff, mypy --strict, bandit, pip-audit nol temuan) — termasuk 1 temuan bandit B101 (`assert` pada jalur produksi, diperbaiki jadi exception eksplisit) dan 1 CVE dependensi transitif (`brotli` via `fonttools[woff]`, dinaikkan via `[tool.uv] constraint-dependencies`).

> ✅ **Status Remediasi Temuan Audit Pasca-Implementasi (25 Oktober 2026):** Seluruh temuan audit dari FASE 4 (**2 CRITICAL, 16 HIGH, 25 MEDIUM, 24 LOW**) telah **100% DIPERBAIKI DAN DIVERIFIKASI**.
> - Celah CRITICAL tenant isolation pada `routers/triage.py` & `routers/ai.py` telah diperbaiki fail-closed.
> - Seluruh celah HIGH (Midtrans fail-open & nominal check, auth revocation, Celery task inclusion, DB row locking, quota reset, invitation replay protection, IDOR assign-lead, prompt injection tone, sanitizer wiring, ROE datetime timezone, CVSS vector pattern) telah diperbaiki dengan pengetesan komprehensif.
> - Seluruh celah MEDIUM & LOW (distributed lock compare-and-delete, WeasyPrint watermark fixed diagonal @page, Gemini header auth, SafeFetcher CGNAT & redirect guard, workspace count limit, quality gates hardening) telah diselesaikan.
> - Suite pengujian meningkat menjadi **330 test lolos (100% pass, 0 fail)** dengan coverage **91.4%**.
> - Skrip `uv run python scripts/check_quality.py` lolos seluruh 5 gerbang mutu (Ruff, Mypy strict, Bandit, Pytest coverage >= 85%, pip-audit) dengan `[SUCCESS] Seluruh Quality Gates Lolos! Kode siap di-commit.` Lihat `DOCS/AUDIT_FINDINGS.md` §5 untuk rincian lengkap perbaikan per ID.

---

### FASE 5: CLI Agent Lintas Platform (`apps/cli`)

> **Tujuan:** Membangun perkakas CLI Python yang mandiri, portabel, dan ramah pengguna di Windows, Mac, dan Linux.

- [ ] **5.1** Setup CLI Entrypoint via `Typer` & `Rich` (`apps/cli/vulnflow/main.py`).
- [ ] **5.2** Perintah `vulnflow configure`:
  - [ ] Simpan token API dan active workspace ke `~/.vulnflow/config.json` (EC-01).
- [ ] **5.3** Perintah `vulnflow setup-tools` (lihat EDGE_CASES_AND_RESILIENCE.md §2: Arsitektur Biner Lintas Platform CLI):
  - [ ] Deteksi otomatis OS & CPU (`platform.system()`, `platform.machine()`).
  - [ ] Download otomatis biner resmi Nuclei dari GitHub Releases ke `~/.vulnflow/bin/`.
- [ ] **5.4** Perintah `vulnflow scan`:
  - [ ] Wrapper eksekusi pemindaian lokal dengan biner Nuclei.
- [ ] **5.5** Parser Streaming JSONL & Nmap XML:
  - [ ] Parser membaca file per baris (*JSON Lines*), tahan terhadap interupsi `Ctrl+C` (EC-06).
  - [ ] Parser Nmap XML menggunakan `defusedxml` (pencegah XML Entity Expansion).
- [ ] **5.6** Perintah `vulnflow push`:
  - [ ] HTTPX client dengan *auto-retry 3x backoff* dan header `Idempotency-Key` (EC-07).
  - [ ] *Graceful degradation:* Notifikasi interaktif jika temuan > 50 item pada paket Free (EC-10).

---

### FASE 6: Web Dashboard SPA (`apps/web`)

> **Tujuan:** Mengimplementasikan antarmuka web modern berbasis Vue 3 (Composition API), Tailwind CSS, dan shadcn-vue. Stack ini sengaja disatukan dengan rubrik wajib mata kuliah Desain Web (Vue 3 Composition API, Vue Router, minimal 5 halaman/8 komponen — lihat `Desweb/DOCS/Minimum Recruitment Proyek Desain Web.md` & `Desweb/DOCS/Dokumentasi_Proyek_Desweb_VulnFlow_AI.docx`), sehingga **satu basis kode `apps/web` ini memenuhi kebutuhan kedua mata kuliah sekaligus**. Pemenuhan ini ditegaskan di tingkat rute, bukan sekadar jumlah: `apps/web` terdiri dari dua kelompok rute yang hidup berdampingan dalam satu router Vue yang sama —
> 1. **Rute Publik (`/`, `/about`, `/solutions`, `/solutions/:id`, `/contact`)** — tidak memerlukan login, berisi 5 halaman wajib Desweb (Home+Live Sandbox demo, Architecture 4-Node, Triage Catalog **mock data**, Finding Detail mock, Audit Booking+simulator Midtrans) sesuai UC-01 s.d. UC-05a pada dokumentasi Desweb di atas — dokumen tersebut menjadi rujukan tunggal untuk detail UI/UX halaman publik ini (tidak diduplikasi di SDD).
> 2. **Rute Terautentikasi (`/app/*`)** — mengharuskan sesi JWT valid (route guard, lihat 6.1), berisi dashboard SaaS VulnFlow AI yang sesungguhnya (Wireframe 1–5 di SDD §4.2 / sub-tugas 6.9–6.15 di bawah) sesuai kebutuhan fungsional IPPL.

- [ ] **6.1** Setup Project Vue 3 (Composition API) + Vite + Tailwind CSS + shadcn-vue + Vue Router (`apps/web/src/router/index.ts`):
  - [ ] Struktur folder mengikuti istilah rubrik Desweb secara literal: `src/assets/`, `src/components/`, `src/pages/` (bukan `src/views/`), `src/router/`, `src/styles/`, `App.vue`.
  - [ ] Navigation guard (`router.beforeEach`) yang membedakan rute Publik (bebas akses) vs rute `/app/*` (wajib JWT valid, redirect ke `/app/login` jika tidak).
- [ ] **6.2** API Client terintegrasi dengan shared Pydantic types (`apps/web/src/services/api.ts`).

#### Rute Publik (Desweb — tanpa login, `src/pages/public/`)
- [ ] **6.3** `/` Home & Live Sandbox: hero section + kanvas Split-Conduit (toggle Sanitizer Mode) sesuai UC-01 Desweb.
- [ ] **6.4** `/about` Security Architecture: diagram pipa 4-Node yang dapat diklik (Local CLI → Scope Gateway → AI Sanitizer → WeasyPrint Engine) sesuai UC-02 Desweb.
- [ ] **6.5** `/solutions` Triage Catalog (mock): layout Master-Detail 40/60 dengan data mock (bukan API asli), search bar, filter badge keparahan, sesuai UC-03 Desweb.
- [ ] **6.6** `/solutions/:id` Finding Detail (mock): radar chart CVSS interaktif, tab remediation & PoC mock, modal dekripsi PoC (UC-04/UC-04a Desweb).
- [ ] **6.7** `/contact` Audit Booking: slider kalkulator jumlah aset, formulir NDA, modal simulasi Midtrans Snap (UC-05/UC-05a Desweb) — **simulasi lead-gen untuk calon klien, terpisah dari billing langganan asli di 6.13**.
- [ ] **6.8** Navbar & Footer publik berfungsi penuh di seluruh 5 rute di atas (memenuhi item "Navigasi" rubrik Desweb).

#### Dashboard Terautentikasi (IPPL — wajib login, `/app/*`, `src/pages/app/`)
> Penomoran "Wireframe N" di bawah ini mengikuti SDD §4.2 secara persis (5 wireframe resmi); halaman pendukung (Login/Registrasi, Workspace/Proyek) bukan bagian dari penomoran itu, diberi label terpisah agar tidak diklaim sebagai wireframe yang sama.
- [ ] **6.9** Halaman Login & Registrasi (MFA modal ready).
- [ ] **6.10** Halaman Ruang Kerja & Pembuatan Proyek (Definisi Target Scope & ROE).
- [ ] **6.11** Wireframe 1 (SDD §4.2.1): Dasbor Utama & Sebaran Metrik CVSS.
- [ ] **6.12** Wireframe 2 (SDD §4.2.2): Papan Triase & Grid Temuan Interaktif:
  - [ ] Filter keparahan, pencarian CWE, modal editor PoC.
  - [ ] Modal Kalkulator CVSS v3.1 interaktif.
  - [ ] Inline dropdown triase status temuan.
- [ ] **6.13** Wireframe 3 (SDD §4.2.3): Editor Interaktif Tinjauan Narasi AI (WYSIWYG) — UC-12:
  - [ ] Rich-text editor, server-side HTML sanitization (stored XSS guard).
  - [ ] Dialog peringatan sebelum "Re-generate AI" menimpa editan manual.
- [ ] **6.14** Wireframe 4 (SDD §4.2.4): Branding & Theme Studio:
  - [ ] Pengatur palet heksadesimal, upload logo, live WYSIWYG preview sampul laporan.
- [ ] **6.15** Wireframe 5 (SDD §4.2.5): Billing & Simulator Midtrans Snap (langganan asli — berbeda dari simulator lead-gen di 6.7):
  - [ ] Tampilan pemantauan kuota laporan real-time.
  - [ ] Integrasi pop-up modal Snap simulator (QRIS / Virtual Account).

---

### FASE 7: Pengujian Mutu Menyeluruh & Uji 18 Kasus Batas (*QA Test Suite*)

> **Tujuan:** Verifikasi komprehensif seluruh sistem terhadap skenario normal dan ekstrem.

- [ ] **7.1** Test Suite Unit & Integrasi API:
  - [ ] Otentikasi & RBAC multi-tenant isolation tests.
  - [ ] Ingestion payload verification tests.
- [ ] **7.2** Test Suite Ketahanan Kasus Batas (`tests/test_resilience/`) — wajib 18/18, mengikuti EDGE_CASES_AND_RESILIENCE.md §6 sebagai daftar kanonik (kedua dokumen harus selalu sinkron):
  - [ ] `test_ec01_multi_workspace_context.py`
  - [ ] `test_ec02_invitation_token_expiry.py`
  - [ ] `test_ec03_orphan_workspace_prevention.py`
  - [ ] `test_ec04_scope_enforcement_cidr.py`
  - [ ] `test_ec05_roe_timezone_boundary.py`
  - [ ] `test_ec06_cli_interrupted_jsonl.py`
  - [ ] `test_ec07_chunked_ingest_idempotency.py`
  - [ ] `test_ec08_dedup_hash_path_differentiation.py`
  - [ ] `test_ec09_nullable_port_rendering.py`
  - [ ] `test_ec10_free_tier_graceful_prompt.py`
  - [ ] `test_ec11_triage_optimistic_locking.py`
  - [ ] `test_ec12_false_positive_report_exclusion.py`
  - [ ] `test_ec13_prompt_injection_sanitization.py`
  - [ ] `test_ec14_ai_in_memory_fallback.py`
  - [ ] `test_ec15_pdf_distributed_lock_double_click.py`
  - [ ] `test_ec16_report_worker_crash_quota_rollback.py`
  - [ ] `test_ec17_presigned_url_dynamic_regeneration.py`
  - [ ] `test_ec18_midtrans_webhook_idempotency.py`
- [ ] **7.3** Verifikasi Akhir Quality Gate:
  - [ ] Jalankan `python scripts/check_quality.py` $\rightarrow$ 100% PASS (Coverage $\ge 85\%$).
- [ ] **7.4** Dokumentasi Pengujian & Lembar Tanda Tangan QA Sign-Off.

---

## 4. Panduan Eksekusi & Pembaruan Status (*How to Track*)

Setiap kali menyelesaikan sebuah sub-tugas:

1. Tandai checklist dari `[ ]` menjadi `[x]`. **Aturan checkbox induk:** sebuah item induk (mis. `0.3`) hanya boleh ditandai `[x]` jika **seluruh** sub-item di bawahnya sudah `[x]`. Induk tanpa sub-item (mis. `0.1`) ditandai `[x]` begitu tugasnya sendiri selesai.
2. Jalankan skrip pemeriksa mutu: `python scripts/check_quality.py`.
3. Lakukan commit Git terstruktur:
   - `feat(contracts): implement finding schemas according to SDD 2.6.1`
   - `feat(database): initialize lean 11 tables with alembic migration`
   - `test(resilience): add test for EC-15 pdf double click distributed lock`

### 4.1 Cakupan Gerbang Mutu per Fase (*Quality Gate Scoping*)
Langkah 2 di atas wajib dijalankan di **setiap** sub-tugas sejak FASE 0 — tetapi ambang batasnya **bertingkat**, bukan satu nilai tetap 85% sejak hari pertama:

| Pemeriksaan | FASE 0 s.d. 6 (kode belum lengkap) | FASE 7 (gerbang akhir) |
| :--- | :--- | :--- |
| Ruff, Mypy `--strict`, Bandit, pip-audit | **0 Error, selalu wajib** — berlaku penuh sejak sub-tugas pertama, tanpa toleransi di fase manapun. | Sama — 0 Error. |
| Pytest & Coverage | Dihitung **proporsional** hanya atas modul yang sudah ditulis sejauh itu (`pytest --cov=<module_yang_sudah_ada>`). Direktori yang belum dibuat (termasuk `tests/test_resilience/` sebelum FASE 7.2) **tidak** menyebabkan galat collection — skrip melaporkan "N/A (belum ada modul untuk fase ini)" dan tetap **lolos**, bukan gagal. | Ambang **85% coverage keseluruhan + 18/18 test resilience PASS** baru ditegakkan secara hard-fail di sini (FASE 7.3), sesuai contoh keluaran §2.3. |

Dengan kata lain: linter/type-checker/security scan menjaga kebersihan kode di setiap commit sejak awal, sementara target coverage 85% dan kelulusan 18 skenario edge case adalah **gerbang akhir proyek (FASE 7)**, bukan syarat setiap sub-tugas individual.
