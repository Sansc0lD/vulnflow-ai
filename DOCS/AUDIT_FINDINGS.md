# LAPORAN VALIDASI, AUDIT KODE, & KONSISTENSI SPESIFIKASI (FASE 0 & FASE 1)

## Platform SaaS VulnFlow AI — Pra-Implementasi FASE 2

**Dokumen Acuan yang Diaudit:**
- [Software Requirements Specification (SRS) v3.5.0](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/SRS.md)
- [Software Design Description (SDD) v1.6.0](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/SDD.md)
- [Matriks Kasus Batas & Ketahanan Sistem (EC-01..18)](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/EDGE_CASES_AND_RESILIENCE.md)
- [Master Tracking Plan (PLAN.md)](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/PLAN.md)

**Cakupan Codebase yang Diaudit:** [`vulnflow-ai/`](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/vulnflow-ai) (FASE 0 & FASE 1)  
**Tanggal Audit:** 20 Oktober 2026  
**Total Temuan:** **16 Temuan** (**4 HIGH**, **8 MEDIUM**, **4 LOW**)  
**Status Remediasi:** **16/16 Diverifikasi & Diperbaiki (20 Oktober 2026)** — seluruh temuan divalidasi langsung terhadap kode/dokumen sebelum diperbaiki; tidak ada temuan yang terbantahkan (false positive). Lihat checklist §4 untuk detail per item. Kode diverifikasi ulang end-to-end (`uv sync --all-packages`, `check_quality.py` → SUCCESS, coverage 94.3%) dan commit awal Git (`7d7da87`) sudah dibuat.

---

## 1. Status Kemajuan Proyek Saat Ini

Berdasarkan pelacakan pada [`PLAN.md`](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/PLAN.md#L14-L27) dan verifikasi langsung pada sistem berkas [`vulnflow-ai/`](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/vulnflow-ai), proyek berada pada posisi **50% (Seluruh Dokumen Spesifikasi + FASE 0 + FASE 1 Selesai, Siap Memasuki FASE 2)**:

| Fase / Komponen | Status di `PLAN.md` | Verifikasi Aktual di Codebase | Bukti & Catatan Kemajuan |
| :--- | :---: | :---: | :--- |
| **Dokumen Spesifikasi** (`SRS v3.5.0`, `SDD v1.6.0`, `EDGE_CASES_AND_RESILIENCE`, `PLAN`) | **100% SELESAI** | **Terverifikasi** | Keempat dokumen utama telah lengkap, menyatukan arsitektur Vue 3 + `shadcn-vue` (rute publik Desweb + rute `/app/*` IPPL) serta 18 skenario `EC-01..EC-18`. Namun masih ditemukan beberapa inkonsistensi internal antar-bab yang dapat berdampak pada FASE 2–5 (lihat Seksi 3). |
| **FASE 0: Monorepo Scaffolding & Environment** (`0.1`–`0.6`) | **100% SELESAI** (6/6) | **Terverifikasi** | Workspace `uv` ([`pyproject.toml`](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/vulnflow-ai/pyproject.toml), [`apps/api/pyproject.toml`](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/vulnflow-ai/apps/api/pyproject.toml), [`apps/cli/pyproject.toml`](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/vulnflow-ai/apps/cli/pyproject.toml), [`packages/contracts/pyproject.toml`](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/vulnflow-ai/packages/contracts/pyproject.toml)), [`docker-compose.yml`](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/vulnflow-ai/docker-compose.yml), [`.env.example`](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/vulnflow-ai/.env.example), [`.gitignore`](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/vulnflow-ai/.gitignore), dan [`scripts/check_quality.py`](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/vulnflow-ai/scripts/check_quality.py) sudah terbentuk. |
| **FASE 1: Pydantic V2 Shared Contracts** (`1.1`–`1.7`) | **100% SELESAI** (7/7) | **Terverifikasi (35/35 test PASS)** | Seluruh 6 modul kontrak di [`packages/contracts/vulnflow_contracts/`](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/vulnflow-ai/packages/contracts/vulnflow_contracts) dan 35 unit test di [`tests/contracts/test_schemas.py`](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/vulnflow-ai/tests/contracts/test_schemas.py) mencapai **100% coverage** pada `packages/contracts` (**94.3%** gabungan dengan stub CLI). |
| **FASE 2: Database Layer (The Lean 11 Tables)** | **0% (Belum Dimulai)** | [`apps/api/app/__init__.py`](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/vulnflow-ai/apps/api/app/__init__.py) baru berupa stub versi | Target pengerjaan berikutnya sesuai [`PLAN.md` §FASE 2](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/PLAN.md#L146-L171). |
| **FASE 3: Domain Core & Security Engines** | **0% (Belum Dimulai)** | Belum ada `app/domain/` atau `app/services/` | Menunggu FASE 2. |
| **FASE 4: FastAPI Routers & Celery Worker** | **0% (Belum Dimulai)** | Belum ada `app/routers/` atau `app/workers/` | Menunggu FASE 2 & 3. |
| **FASE 5: CLI Agent Lintas Platform** | **0% (Belum Dimulai)** | [`apps/cli/vulnflow/main.py`](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/vulnflow-ai/apps/cli/vulnflow/main.py) baru berupa stub `--version` | Stub CLI berjalan (`vulnflow-cli 0.1.0`). |
| **FASE 6: Web Dashboard SPA (Vue 3)** | **0% (Belum Dimulai)** | `apps/web/` masih kosong | Menunggu FASE 4. |
| **FASE 7: QA & Resilience Test Suite** | **0% (Belum Dimulai)** | `tests/test_resilience/` baru berisi `.gitkeep` | Menunggu FASE 2–6. |

### Bukti Eksekusi Quality Gate Saat Ini
```text
$ uv run python scripts/check_quality.py
[1/5] Menjalankan Ruff Formatter & Linter...           [✓ PASS]
[2/5] Menjalankan Mypy Strict Type Check...            [✓ PASS]
[3/5] Menjalankan Bandit Security SAST...              [✓ PASS]
[4/5] Menjalankan Pytest & Evaluasi Coverage...        [✓ PASS] (Coverage: 94.3%)
[5/5] Menjalankan Kerentanan Dependensi (Audit)...     [✓ PASS]

[SUCCESS] Seluruh Quality Gates Lolos! Kode siap di-commit.
```

---

## 2. Evaluasi Best Practice & Clean Code (FASE 0 & FASE 1)

Aspek implementasi FASE 0 dan FASE 1 yang sudah memenuhi standar rekayasa perangkat lunak modern:

1. **Zero-Trust Input Validation (`ConfigDict(extra="forbid")`):** Seluruh 22 kelas `BaseModel` di [`packages/contracts/vulnflow_contracts/`](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/vulnflow-ai/packages/contracts/vulnflow_contracts) menolak field tak dikenal secara default, sesuai prinsip *Zero Trust Data Ingestion* ([`SDD.md` §1.3](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/SDD.md#L105)).
2. **Idiom Modern Python 3.12+ & Pydantic V2:** Penggunaan `enum.StrEnum`, tipe union `X | None`, `Field(default_factory=list)` (bebas bug *mutable default argument*), dan pemisahan paket workspace `uv` (`apps/api`, `apps/cli`, `packages/contracts`) bersih dan modular.
3. **Kesesuaian Kontrak terhadap Contoh Payload SDD §2.6.1 & §2.6.3:** Seluruh contoh JSON pada SDD §2.6.1.1 s.d. §2.6.1.7 dan §2.6.3 telah diuji *round-trip* di [`tests/contracts/test_schemas.py`](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/vulnflow-ai/tests/contracts/test_schemas.py#L1-L308) dengan **100% statement & branch coverage** pada `packages/contracts`.
4. **Manajemen Kredensial Infrastruktur:** [`docker-compose.yml`](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/vulnflow-ai/docker-compose.yml#L10) menggunakan sintaks `${VAR:?Set VAR in .env}` sehingga gagal cepat (*fail-fast*) apabila `.env` belum dikonfigurasi, tanpa membocorkan password default di repositori.

---

## 3. Daftar Temuan Audit Lengkap (16 Temuan)

### Ringkasan Matriks Temuan

| ID | Prioritas | Kategori | Komponen / Dokumen Terdampak | Ringkasan Masalah |
| :---: | :---: | :--- | :--- | :--- |
| **HIGH-01** | **HIGH** | Infrastruktur Docker | `vulnflow-ai/docker-compose.yml` | Healthcheck container `redis` menggunakan `$$REDIS_PASSWORD` tanpa blok `environment:`, sehingga selalu `unhealthy` (`NOAUTH`). |
| **HIGH-02** | **HIGH** | Kontrak vs Skema DB | `auth_schemas.py` vs `SDD.md §2.4.2` | Konflik enum role RBAC: `'OWNER'` di kontrak API vs `'MANAGER'` di Kamus Data Tabel 3 `workspace_members`. |
| **HIGH-03** | **HIGH** | Kontrak & DB (`EC-08`) | `finding_schemas.py` & `SDD.md §2.4.2` | Tidak ada field/kolom `endpoint_path` pada `UnifiedVulnerabilityFinding`, `ManualFindingRequest`, & tabel `findings` untuk rumus `dedup_hash` `EC-08`. |
| **HIGH-04** | **HIGH** | Kontrak AI (`EC-14`) | `ai_schemas.py` vs `SDD.md §2.6.2.2` & `SD-02` | Struktur JSON di System Prompt LLM §2.6.2.2 berbeda total dari `NarrativeContent`, serta `AINarrativeResponse` belum memiliki field `is_fallback: bool = False`. |
| **MED-01** | **MEDIUM** | Type Checking (Mypy) | `pyproject.toml` & `vulnflow_contracts` | Belum ada marker `py.typed` (PEP 561) dan `mypy --strict` gagal (`[import-untyped]`) pada `boto3`, `celery`, `weasyprint`, & `defusedxml`. |
| **MED-02** | **MEDIUM** | Tooling / DX | `scripts/check_quality.py` | Gagal dengan exit code `127` jika `uv` tidak berada di default `PATH` shell Windows. |
| **MED-03** | **MEDIUM** | Quality Gate Script | `scripts/check_quality.py` | Output kegagalan `pytest` dibuang (`_`), risiko membaca `coverage.json` basi saat collection error, & `step_ruff()` belum memeriksa `tests/` + `scripts/`. |
| **MED-04** | **MEDIUM** | Konsistensi Skema DB | `SDD.md §2.4.2` vs `PLAN.md` & `EDGE_CASES` | 5 diskrepansi kolom DB (`is_quarantined`, `roe_start_date`/`timezone`, `tokens_consumed` vs `tokens_used`, `storage_path`/`watermark_applied`, case `payment_status`). |
| **MED-05** | **MEDIUM** | Kontrak Billing | `billing_schemas.py` | `MidtransWebhookPayload` dengan `extra="forbid"` akan menolak field tambahan standar webhook Midtrans asli, dan regex `signature_key` hanya menerima hex lowercase. |
| **MED-06** | **MEDIUM** | Kontrak Auth (`EC-02`) | `auth_schemas.py` | `RegisterRequest` belum membatasi `password <= 128` karakter & bebas null byte `\0` (`UC-01 E2`), batas panjang `full_name`/`workspace_name` > DB, & belum ada `invitation_token` (`EC-02`). |
| **MED-07** | **MEDIUM** | Keamanan Kode Referensi | `SDD.md §2.5.4` & `EDGE_CASES §2.2, §5.3` | Snippet referensi `safe_url_fetcher` & `ensure_tools_installed` berpotensi gagal di Mypy `--strict` & Bandit (`B310`/`B202`), serta celah bypass IPv4-mapped IPv6 SSRF. |
| **MED-08** | **MEDIUM** | Spesifikasi Auth | `SRS.md` vs `SDD.md §2.6.1.4` | Konflik mekanisme sesi: Access Token 15m Cookie + Refresh Token DB di SRS vs Bearer Token 24 jam (`86400s`) stateless `token_version` di SDD & kontrak. |
| **LOW-01** | **LOW** | Git Hygiene | `vulnflow-ai/.git` & `coverage.json` | Belum ada commit Git awal untuk FASE 0 & FASE 1, serta file artefak `coverage.json` tertinggal di working tree. |
| **LOW-02** | **LOW** | Reproducibility | `vulnflow-ai/docker-compose.yml` | Penggunaan floating tag `minio/minio:latest` (sedangkan Postgres & Redis sudah memakai tag versi terkunci). |
| **LOW-03** | **LOW** | Struktur Dokumen | `DOCS/SDD.md` | Penomoran Daftar Isi (§2.3, §2.5, Bab 5) dan sub-heading `#### 3.1.1`/`3.1.2` di dalam §2.6.0 belum sinkron, serta duplikasi diagram Mermaid §2.5.2 di §2.6.4. |
| **LOW-04** | **LOW** | Sinkronisasi Dokumen | `SRS.md`, `SDD.md`, `PLAN.md` | Checklist Wireframe Editor AI (`UC-12`) di `PLAN.md` FASE 6, sisa penyebutan `Argparse`/`xmltodict`, perbedaan angka kuota Pro (50 vs 30), TTL undangan (24j vs 7h), & HTTP 422 vs 413. |

---

### A. Detail Temuan Prioritas Tinggi (`HIGH`)

#### `[HIGH-01]` Healthcheck Container `redis` di `docker-compose.yml` Pasti Gagal (`unhealthy`)
- **Lokasi:** [`vulnflow-ai/docker-compose.yml` baris 24–39](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/vulnflow-ai/docker-compose.yml#L24-L39)
- **Bukti Kode:**
  ```yaml
  redis:
    image: redis:7.2-alpine
    container_name: vulnflow-redis
    restart: unless-stopped
    command: ["redis-server", "--requirepass", "${REDIS_PASSWORD:?Set REDIS_PASSWORD in .env}"]
    ...
    healthcheck:
      test: ["CMD-SHELL", "REDISCLI_AUTH=$$REDIS_PASSWORD redis-cli ping | grep PONG"]
  ```
- **Analisis Masalah:**
  - Pada `command`, `${REDIS_PASSWORD}` diinterpolasi oleh Docker Compose dari `.env` di mesin host.
  - Pada `healthcheck.test`, penulisan `$$REDIS_PASSWORD` menghasilkan literal `$REDIS_PASSWORD` yang dievaluasi oleh shell `/bin/sh` di dalam container `redis`.
  - Karena service `redis` **tidak memiliki blok `environment:`**, variabel `$REDIS_PASSWORD` di dalam container bernilai string kosong (`""`). Akibatnya `redis-cli ping` selalu ditolak dengan `NOAUTH Authentication required` dan status container menjadi `unhealthy`.
- **Rekomendasi Perbaikan:**
  - Gunakan interpolasi host langsung `REDISCLI_AUTH=${REDIS_PASSWORD} redis-cli ping | grep PONG`, atau tambahkan blok `environment: REDIS_PASSWORD: ${REDIS_PASSWORD:?Set REDIS_PASSWORD in .env}` pada service `redis`.

---

#### `[HIGH-02]` Konflik Nilai Enum Role RBAC (`OWNER` vs `MANAGER`) antara Kontrak FASE 1 dan Kamus Data DB FASE 2
- **Lokasi:**
  - [`packages/contracts/vulnflow_contracts/auth_schemas.py` baris 30–36](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/vulnflow-ai/packages/contracts/vulnflow_contracts/auth_schemas.py#L30-L36)
  - [`DOCS/SDD.md` §2.4.2 Tabel 3 `workspace_members` baris 866](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/SDD.md#L866)
  - [`DOCS/SDD.md` AD-04 baris 596](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/SDD.md#L596) & [`DOCS/SRS.md` UC-01 baris 491](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/SRS.md#L491)
- **Analisis Masalah:**
  - [`WorkspaceRole`](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/vulnflow-ai/packages/contracts/vulnflow_contracts/auth_schemas.py#L30-L35), [`SDD.md` §2.6.1.4](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/SDD.md#L1326), [`PLAN.md` FASE 4.3](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/PLAN.md#L211), dan [`EC-03`](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/EDGE_CASES_AND_RESILIENCE.md#L130) mendefinisikan enum role sebagai `'OWNER' | 'PENTESTER' | 'VIEWER'`.
  - Sebaliknya, Kamus Data [`SDD.md` §2.4.2 Tabel 3 `workspace_members`](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/SDD.md#L866) (yang diinstruksikan [`PLAN.md` baris 148](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/PLAN.md#L148) disalin *"tanpa deviasi"*) mendefinisikan `'MANAGER' | 'PENTESTER' | 'VIEWER'`.
  - Jika tabel `workspace_members` di FASE 2 menyimpan `'MANAGER'`, maka response `POST /api/v1/auth/login` (`TokenResponse` $\rightarrow$ `UserDTO`) akan melempar `ValidationError` dari Pydantic.
- **Rekomendasi Perbaikan:**
  - Seragamkan nilai enum role menjadi `MANAGER`, `PENTESTER`, `VIEWER` pada Kamus Data SDD §2.4.2 dan model SQLAlchemy FASE 2.

---

#### `[HIGH-03]` Ketiadaan Field `endpoint_path` / `path` pada `UnifiedVulnerabilityFinding`, `ManualFindingRequest`, & Tabel `findings` untuk Mendukung `EC-08`
- **Lokasi:**
  - [`packages/contracts/vulnflow_contracts/finding_schemas.py` baris 58–72 & 99–113](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/vulnflow-ai/packages/contracts/vulnflow_contracts/finding_schemas.py#L58-L72)
  - [`DOCS/SDD.md` §2.4.2 Tabel 7 `findings` baris 905](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/SDD.md#L905)
  - [`DOCS/EDGE_CASES_AND_RESILIENCE.md` §5.2 baris 193–201](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/EDGE_CASES_AND_RESILIENCE.md#L193-L201)
  - [`DOCS/PLAN.md` FASE 3.1 baris 179](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/PLAN.md#L179)
- **Analisis Masalah:**
  - Kasus batas `EC-08` mewajibkan formula hash deduplikasi menyertakan `path` endpoint:
    $$\text{dedup\_hash} = \text{SHA256}(\text{project\_id} + \text{cwe\_id} + \text{host} + \text{port} + \text{endpoint\_path})$$
    agar dua celah yang sama pada endpoint berbeda (mis. SQLi di `/api/v1/users` vs `/api/v1/orders` pada host dan port yang sama) tidak saling menimpa.
  - Namun [`UnifiedVulnerabilityFinding`](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/vulnflow-ai/packages/contracts/vulnflow_contracts/finding_schemas.py#L58-L72) dan [`ManualFindingRequest`](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/vulnflow-ai/packages/contracts/vulnflow_contracts/finding_schemas.py#L99-L113) menerapkan `extra="forbid"` dan hanya memiliki `target_host` serta `target_port` — belum memiliki field opsional `endpoint_path: str = ""`.
  - Selain itu, Tabel 7 `findings` di [`SDD.md` §2.4.2 baris 905](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/SDD.md#L905) belum mencantumkan kolom `endpoint_path` dan masih mencantumkan rumus lama `SHA-256(project_id + host + port + proto + cwe_id)`.
- **Rekomendasi Perbaikan:**
  - Tambahkan field opsional `endpoint_path: str = Field(default="", max_length=500)` pada `UnifiedVulnerabilityFinding` dan `ManualFindingRequest`, serta tambahkan kolom `endpoint_path` pada tabel `findings` di FASE 2.

---

#### `[HIGH-04]` Konflik Skema JSON Output AI antara `ai_schemas.py` (`SDD §2.6.1.3`) vs System Prompt LLM (`SDD §2.6.2.2`) & Absennya Flag `is_fallback` (`UC-11b` / `EC-14`)
- **Lokasi:**
  - [`packages/contracts/vulnflow_contracts/ai_schemas.py` baris 17–40](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/vulnflow-ai/packages/contracts/vulnflow_contracts/ai_schemas.py#L17-L40)
  - [`DOCS/SDD.md` §2.6.1.3 baris 1254–1270](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/SDD.md#L1254-L1270) vs [`DOCS/SDD.md` §2.6.2.2 baris 1507–1519](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/SDD.md#L1507-L1519)
  - [`DOCS/SDD.md` AD-02 baris 437 & 468](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/SDD.md#L437) & [`DOCS/SDD.md` §3.2 SD-02 baris 1716](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/SDD.md#L1716)
  - [`DOCS/SRS.md` UC-11b baris 872](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/SRS.md#L872)
- **Analisis Masalah:**
  1. **Ketidakcocokan Kunci JSON System Prompt vs Kontrak Pydantic:**
     - Pada [`ai_schemas.py`](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/vulnflow-ai/packages/contracts/vulnflow_contracts/ai_schemas.py#L17-L31) (sesuai SDD §2.6.1.3), `NarrativeContent` mengharapkan kunci:
       - `executive_summary: str`
       - `business_impact: str`
       - `remediations: list[RemediationItem]` dengan item `{cwe_id, vuln_title, remediation_guidance}`
     - Sebaliknya, pada [`SDD.md` §2.6.2.2 baris 1508–1519](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/SDD.md#L1508-L1519), *System Prompt* memerintahkan LLM menghasilkan JSON dengan kunci:
       - `executive_summary`
       - `overall_risk_rating`
       - `business_impact_analysis`
       - `mitigation_priorities` berisi `{vulnerability, short_term_fix, long_term_strategy}`
     - Karena `NarrativeContent` menerapkan `ConfigDict(extra="forbid")`, jika prompt §2.6.2.2 dipakai di FASE 4.6 (`AIRouter`), maka respons LLM **pasti selalu gagal validasi skema** dan selalu memicu fallback.
  2. **Absennya Field `is_fallback` pada `AINarrativeResponse`:**
     - [`AINarrativeResponse`](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/vulnflow-ai/packages/contracts/vulnflow_contracts/ai_schemas.py#L33-L40) hanya memiliki `narratives`, `tokens_consumed`, dan `generated_at`.
     - Padahal [`SRS.md` UC-11b baris 872](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/SRS.md#L872), [`SDD.md` AD-02 baris 437](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/SDD.md#L437), dan [`SDD.md` SD-02 baris 1716](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/SDD.md#L1716) mewajibkan backend mengembalikan penanda fallback pada respons `HTTP 200 OK` agar UI Web menampilkan banner pemberitahuan fallback (dan diuji oleh `test_ec14_ai_in_memory_fallback.py`).
- **Rekomendasi Perbaikan:**
  1. Selaraskan spesifikasi JSON pada System Prompt SDD §2.6.2.2 agar persis menggunakan skema `NarrativeContent`.
  2. Tambahkan `is_fallback: bool = False` pada `AINarrativeResponse` (dengan default `False`, kompatibilitas terhadap contoh JSON SDD §2.6.1.3 tetap terjaga 100%).

---

### B. Detail Temuan Prioritas Menengah (`MEDIUM`)

#### `[MED-01]` Paket `vulnflow-contracts` Belum Memiliki Marker PEP 561 `py.typed` & Konfigurasi Mypy Belum Meng-handle `boto3`, `celery`, `weasyprint`, dan `defusedxml`
- **Lokasi:** `packages/contracts/vulnflow_contracts/` & [`vulnflow-ai/pyproject.toml` baris 47–53](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/vulnflow-ai/pyproject.toml#L47-L53)
- **Bukti Pemeriksaan:**
  ```text
  $ .\.venv\Scripts\mypy.exe --strict -c "import fastapi, uvicorn, sqlalchemy, alembic, psycopg, celery, redis, argon2, jwt, cryptography, weasyprint, boto3, httpx, typer, rich, defusedxml"
  <string>:1: error: Skipping analyzing "celery": module is installed, but missing library stubs or py.typed marker  [import-untyped]
  <string>:1: error: Skipping analyzing "weasyprint": module is installed, but missing library stubs or py.typed marker  [import-untyped]
  <string>:1: error: Skipping analyzing "boto3": module is installed, but missing library stubs or py.typed marker  [import-untyped]
  <string>:1: error: Library stubs not installed for "defusedxml"  [import-untyped]
  ```
- **Rekomendasi Perbaikan:**
  - Buat berkas kosong `packages/contracts/vulnflow_contracts/py.typed`.
  - Tambahkan `types-defusedxml` ke dalam dependency group `dev` di root `pyproject.toml`.
  - Tambahkan konfigurasi override di `pyproject.toml`:
    ```toml
    [[tool.mypy.overrides]]
    module = ["boto3.*", "botocore.*", "celery.*", "weasyprint.*"]
    ignore_missing_imports = true
    ```

---

#### `[MED-02]` `scripts/check_quality.py` Gagal (`exit 127`) Jika `uv` Tidak Ada di Default `PATH` Shell
- **Lokasi:** [`vulnflow-ai/scripts/check_quality.py` baris 32–41](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/vulnflow-ai/scripts/check_quality.py#L32-L41)
- **Analisis Masalah:**
  - Pada mesin Windows, `uv.exe` sering terinstal di `%APPDATA%\Python\Python3XX\Scripts\uv.exe` atau `~/.local/bin/uv.exe` yang belum tentu dimuat pada sesi shell non-interaktif. Menjalankan `python scripts/check_quality.py` sesuai contoh [`PLAN.md` §2.3](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/PLAN.md#L79) menghasilkan exit code `127`.
- **Rekomendasi Perbaikan:**
  - Tambahkan fallback pencarian `uv` di lokasi standar (`sysconfig.get_path("scripts", "nt_user")`, `~/.local/bin`, `~/.cargo/bin`) atau fallback langsung ke interpreter/scripts di `.venv` lokal (`ROOT / ".venv"`).

---

#### `[MED-03]` `scripts/check_quality.py` Membuang Output Kegagalan Pytest, Berisiko Membaca `coverage.json` Basi, & Tidak Melinting `tests/` + `scripts/`
- **Lokasi:** [`vulnflow-ai/scripts/check_quality.py` baris 80–160](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/vulnflow-ai/scripts/check_quality.py#L80-L160)
- **Analisis Masalah:**
  1. **Output kegagalan Pytest dibuang:** Pada `_run_pytest_with_coverage()`, pemanggilan `code, _ = run(["pytest", ...])` membuang seluruh output stdout/stderr. Jika ada unit test yang gagal pada mode proporsional, pengembang hanya melihat `[✗ FAIL]` tanpa nama test atau traceback kegagalannya.
  2. **Risiko membaca `coverage.json` basi (*stale file*):** Berkas `coverage.json` tidak dihapus sebelum menjalankan `pytest` (dan tertinggal di working tree). Apabila `pytest` gagal saat *collection* (mis. `ImportError` / `SyntaxError`), `pytest-cov` tidak memperbarui `coverage.json`, sehingga `_read_coverage_pct()` membaca angka dari eksekusi lama.
  3. **Cakupan Ruff:** `step_ruff()` hanya memeriksa `EXISTING_SOURCE_DIRS` dan belum memeriksa kode di dalam `tests/` maupun `scripts/`.
- **Rekomendasi Perbaikan:**
  - Hapus `coverage.json` sebelum menjalankan `pytest` (dan hapus kembali setelah dibaca di blok `finally`), tangkap dan tampilkan output `pytest` ketika `exit_code != 0`, serta sertakan `"tests"` dan `"scripts"` pada `step_ruff()`.

---

#### `[MED-04]` Diskrepansi Nama & Keberadaan Kolom antara Kamus Data `SDD.md §2.4.2` dan `PLAN.md` / `EDGE_CASES_AND_RESILIENCE.md`
- **Lokasi:** [`DOCS/SDD.md` §2.4.2 baris 839–960](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/SDD.md#L839-L960) vs [`DOCS/PLAN.md` FASE 2.3 baris 148–163](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/PLAN.md#L148-L163)
- **Analisis Masalah:** [`PLAN.md` baris 148](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/PLAN.md#L148) menginstruksikan FASE 2 mengacu penuh pada SDD §2.4.2 *"tanpa deviasi"*, tetapi terdapat 5 ketidaksinkronan kolom yang dibutuhkan oleh FASE 3, 4, dan 7:
  1. **Tabel `findings` (Tabel 7):** Belum mencantumkan kolom `is_quarantined (BOOLEAN, Default: false)` di SDD §2.4.2, padahal diwajibkan oleh [`PLAN.md` FASE 3.3](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/PLAN.md#L186), [`SDD.md` §2.7.2](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/SDD.md#L1633), [`SDD.md` DTM baris 2061](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/SDD.md#L2061), dan [`EDGE_CASES_AND_RESILIENCE.md` §3.3](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/EDGE_CASES_AND_RESILIENCE.md#L120).
  2. **Tabel `projects` (Tabel 6):** SDD §2.4.2 mendefinisikan `audit_start_date (DATE)` & `audit_end_date (DATE)` tanpa kolom `timezone`, sedangkan [`EC-05`](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/EDGE_CASES_AND_RESILIENCE.md#L132) dan [`SDD.md` §2.7.1 EC-05](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/SDD.md#L1613) mewajibkan `TIMESTAMPTZ` + atribut `timezone` proyek (dan menyebut `roe_start_date` / `roe_end_date`).
  3. **Tabel `ai_narratives` (Tabel 9):** SDD §2.4.2 menulis `tokens_used`, sedangkan [`PLAN.md` baris 161](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/PLAN.md#L161), [`SDD.md` DTM baris 2067](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/SDD.md#L2067), dan `AINarrativeResponse` menulis `tokens_consumed`.
  4. **Tabel `reports` (Tabel 10):** SDD §2.4.2 menulis `pdf_artifact_url` dan `is_watermarked`, sedangkan [`PLAN.md` baris 162](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/PLAN.md#L162), [`EDGE_CASES_AND_RESILIENCE.md` §5.4 baris 268](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/EDGE_CASES_AND_RESILIENCE.md#L268), [`SRS.md` UC-04 E2 baris 587](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/SRS.md#L587), dan [`SDD.md` DTM baris 2074](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/SDD.md#L2074) menulis `storage_path` dan `watermark_applied`.
  5. **Tabel `subscriptions` (`payment_status`, Tabel 4):** SDD §2.4.2 mendefinisikan enum uppercase `'PENDING' | 'SETTLEMENT' | 'EXPIRE' | 'CANCEL'`, tetapi [`SDD.md` SD-04 baris 1828](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/SDD.md#L1828) menulis `'EXPIRED'` dan [`EDGE_CASES_AND_RESILIENCE.md` EC-18 baris 145](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/EDGE_CASES_AND_RESILIENCE.md#L145) menulis huruf kecil `'settlement'`.

---

#### `[MED-05]` `MidtransWebhookPayload` di `billing_schemas.py` Terlalu Ketat terhadap Payload Eksternal Midtrans (`extra="forbid"` & Hex Lowercase-Only)
- **Lokasi:** [`packages/contracts/vulnflow_contracts/billing_schemas.py` baris 44–60](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/vulnflow-ai/packages/contracts/vulnflow_contracts/billing_schemas.py#L44-L60)
- **Analisis Masalah:**
  1. Payload webhook dari server Midtrans asli/sandbox selalu menyertakan field standar tambahan di luar 7 field contoh SDD §2.6.3.2 (seperti `transaction_id`, `fraud_status`, `currency`, `merchant_id`, `status_message`). Dengan `ConfigDict(extra="forbid")`, webhook asli dari Midtrans Sandbox akan ditolak dengan `HTTP 422`.
  2. Regex `signature_key` menggunakan `r"^[0-9a-f]{128}$"` (hanya huruf kecil), berbeda dengan `ThemeOptions` di `report_schemas.py` yang menggunakan hex case-insensitive.
- **Rekomendasi Perbaikan:**
  - Gunakan `ConfigDict(extra="ignore")` khusus untuk model webhook eksternal `MidtransWebhookPayload` (atau tambahkan field opsional standar Midtrans) dan ubah regex `signature_key` menjadi `r"^[0-9a-fA-F]{128}$"`.

---

#### `[MED-06]` Validasi `RegisterRequest` (`auth_schemas.py`) Belum Menegakkan Batas DoS Password (`max_length=128`, Null Byte) & `invitation_token` (`EC-02`)
- **Lokasi:** [`packages/contracts/vulnflow_contracts/auth_schemas.py` baris 16–47](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/vulnflow-ai/packages/contracts/vulnflow_contracts/auth_schemas.py#L16-L47)
- **Analisis Masalah:**
  1. [`SRS.md` UC-01 E2 baris 498](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/SRS.md#L498) secara spesifik mewajibkan lapisan validasi skema menolak `password` > 128 karakter atau yang memuat karakter null byte `\0` dengan `HTTP 422` sebelum masuk ke hashing Argon2id (mencegah serangan DoS komputasi). Saat ini `_validate_password_complexity` hanya memeriksa `len(password) < 8`.
  2. `full_name` dan `workspace_name` mengizinkan `max_length=255`, melebihi batas kolom DB di SDD §2.4.2 (`users.full_name VARCHAR(100)`, `workspaces.name VARCHAR(150)`).
  3. Skenario `EC-02` ([`SRS.md` UC-01 2a baris 495](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/SRS.md#L495)) membutuhkan field opsional `invitation_token: str | None = None`.

---

#### `[MED-07]` Potensi Kegagalan SAST Bandit & Mypy Strict pada Contoh Kode Referensi di `SDD.md §2.5.4` dan `EDGE_CASES_AND_RESILIENCE.md §2.2 & §5.3`
- **Lokasi:**
  - [`DOCS/SDD.md` §2.5.4 `safe_url_fetcher` baris 1047–1067](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/SDD.md#L1047-L1067)
  - [`DOCS/EDGE_CASES_AND_RESILIENCE.md` §2.2 `ensure_tools_installed` baris 81–84](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/EDGE_CASES_AND_RESILIENCE.md#L81-L84)
  - [`DOCS/EDGE_CASES_AND_RESILIENCE.md` §5.3 `compile_pdf` baris 218–235](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/EDGE_CASES_AND_RESILIENCE.md#L218-L235)
- **Analisis Masalah:** Jika contoh kode di dokumen disalin langsung pada FASE 3–5:
  1. Pada `safe_url_fetcher` (`SDD.md §2.5.4`), `parsed.hostname` bertipe `str | None` sehingga gagal di `mypy --strict`, serta daftar manual `BLOCKED_IP_NETWORKS` belum memblokir `0.0.0.0/8`, IPv6 link-local `fe80::/10`, unique-local `fc00::/7`, dan IPv4-mapped IPv6 `::ffff:127.0.0.1` / `::ffff:169.254.169.254` (sebaiknya gunakan properti `ip.is_private`, `ip.is_loopback`, `ip.is_link_local`, `ip.is_reserved`, `ip.is_unspecified`, dan `ip.ipv4_mapped`).
  2. Pada `ensure_tools_installed` (`EDGE_CASES_AND_RESILIENCE.md §2.2`), `urllib.request.urlretrieve(...)` dan `zip_ref.extract(...)` akan memicu pelanggaran **Bandit B310** dan **B202** pada `check_quality.py` (gunakan `httpx` + validasi anggota zip).
  3. Pada `compile_pdf` (`EDGE_CASES_AND_RESILIENCE.md §5.3`), contoh return dict belum menyertakan `message` dan `status_url` yang diwajibkan oleh kontrak `CompilePDFAcceptedResponse`.

---

#### `[MED-08]` Konflik Spesifikasi Token Sesi JWT (TTL 15 Menit Ed25519 Cookie vs 24 Jam Bearer Token) antara `SRS.md` dan `SDD.md`
- **Lokasi:** [`DOCS/SRS.md` FR-AUTH-002 & UC-02 baris 281, 514–515](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/SRS.md#L281) vs [`DOCS/SDD.md` §2.6.1.4 baris 1293–1295](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/SDD.md#L1293-L1295) & [`auth_schemas.py`](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/vulnflow-ai/packages/contracts/vulnflow_contracts/auth_schemas.py#L60-L72).
- **Analisis Masalah:**
  - `SRS.md` menyebutkan Access Token berlaku **15 menit** (`900` detik), ditandatangani dengan **Ed25519**, serta disimpan dalam `HTTP-Only, Secure, SameSite=Strict Cookie` bersama Refresh Token 7 hari yang *"tersimpan terenkripsi di basis data"* (padahal di 11 tabel SDD §2.4.2 tidak ada tabel `refresh_tokens`).
  - `SDD.md §2.6.1.4` dan `auth_schemas.py` (`RegisterResponse` / `TokenResponse`) mengembalikan `token_type: "bearer"`, `expires_in: 86400` (**24 jam**), dan menggunakan klaim `token_version` untuk revokasi stateless.
- **Rekomendasi Perbaikan:**
  - Pastikan implementasi FASE 4.2 (`AuthRouter`) mengacu pada kontrak SDD §2.6.1.4 (`Bearer` token dengan verifikasi `users.token_version`).

---

### C. Detail Temuan Prioritas Rendah (`LOW`)

#### `[LOW-01]` Belum Ada Git Commit Awal di `vulnflow-ai/.git` & Berkas `coverage.json` Tertinggal di Working Tree
- **Lokasi:** `vulnflow-ai/.git` & `vulnflow-ai/coverage.json`
- **Analisis Masalah:** Seluruh berkas FASE 0 & FASE 1 masih berstatus untracked (`??`) tanpa commit sama sekali (`fatal: your current branch 'main' does not have any commits yet`), padahal [`PLAN.md` §4](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/PLAN.md#L327-L330) menginstruksikan commit terstruktur per sub-tugas/fase. Selain itu, `coverage.json` hasil eksekusi `check_quality.py` tertinggal di root `vulnflow-ai/`.

---

#### `[LOW-02]` Penggunaan Floating Tag `minio/minio:latest` di `docker-compose.yml`
- **Lokasi:** [`vulnflow-ai/docker-compose.yml` baris 42](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/vulnflow-ai/docker-compose.yml#L42)
- **Analisis Masalah:** Service `postgres:16-alpine` dan `redis:7.2-alpine` sudah menggunakan versi terkunci, tetapi `minio` masih menggunakan `minio/minio:latest` yang berisiko merusak *reproducible builds* ([`SRS.md` NFR-MAINT-002](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/SRS.md#L271)).

---

#### `[LOW-03]` Kerusakan Penomoran Daftar Isi & Sub-Heading di `SDD.md` v1.6.0 serta Duplikasi Diagram §2.5.2 / §2.6.4
- **Lokasi:** [`DOCS/SDD.md` baris 44–88](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/SDD.md#L44-L88), [baris 997–1021](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/SDD.md#L997-L1021), [baris 1076–1102](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/SDD.md#L1076-L1102), [baris 1575–1598](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/SDD.md#L1575-L1598), [baris 2043–2086](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/SDD.md#L2043-L2086)
- **Analisis Masalah:**
  1. **Daftar Isi §2.3 (baris 48):** Menulis `2.3.4 State Machine Diagram`, padahal di isi dokumen `2.3.4` adalah `Activity Diagram 4 (AD-04)` (baris 564) dan `State Machine Diagram` adalah `2.3.5` (baris 665).
  2. **Daftar Isi §2.5 (baris 54–57):** Belum mencantumkan `2.5.4 Pengerasan Keamanan PDF Generator: Custom Safe URL Fetcher (Anti-SSRF)` (baris 1029).
  3. **Daftar Isi Bab 5 (baris 87):** Menulis `5. Bab 5: Penutup & Lembar Pengesahan Desain Teknis`, padahal `BAB 5` di baris 2043 adalah `MATRIKS KETERLACAKAN DESAIN SISTEM (DTM)` dan `Penutup` berada di `BAB 6` (baris 2084).
  4. **Penomoran Sub-Heading salah di dalam §2.6.0 (baris 1076 & 1097):** Di bawah `#### 2.6.0 Ikhtisar Antarmuka`, terdapat heading `#### 3.1.1 Antarmuka Klien Baris Perintah` dan `#### 3.1.2 Antarmuka Web Dashboard`.
  5. **Duplikasi Diagram:** Diagram Mermaid `Protokol Komunikasi Jaringan` di `§2.5.2` (baris 999–1021) terduplikasi identik di `§2.6.4` (baris 1577–1597).

---

#### `[LOW-04]` Ketidaksinkronan Kecil Antar-Bagian di `SRS.md`, `SDD.md`, dan `PLAN.md`
1. **Checklist Wireframe Editor Narasi AI (`UC-12`) di `PLAN.md` FASE 6:** Penomoran Wireframe 1–5 di [`PLAN.md` FASE 6.9–6.13](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/PLAN.md#L275-L285) menggeser daftar wireframe dari [`SDD.md` §4.2](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/SDD.md#L1895-L2012) sehingga halaman **Editor Interaktif Tinjauan Narasi AI (WYSIWYG)** belum tercantum eksplisit sebagai item checklist di FASE 6.
2. **Referensi Pustaka CLI Lama di Narasi `SRS.md` & `SDD.md`:** [`SDD.md` §2.2.2](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/SDD.md#L174) & [`§4.1.1`](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/SDD.md#L1845-L1849) masih menulis `Argparse` dan subcommand `vulnflow auth`, serta [`SRS.md` §2.4.1](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/SRS.md#L177) masih menulis `xmltodict`, sedangkan `PLAN.md` FASE 5 dan `apps/cli/pyproject.toml` sudah menggunakan **`Typer` + `Rich`**, subcommand `vulnflow configure`, dan **`defusedxml`**.
3. **Angka Kuota Pro, TTL Undangan, Kode HTTP Batch Free, & Versi Penutup:**
   - Kuota Pro Tier: `SRS.md FR-SUB-001` (baris 316) menyebut `50 laporan/bulan`, sedangkan `SDD.md §2.4.2` (baris 873) menyebut `30 laporan/bulan`.
   - TTL Invitation Token: `SRS.md UC-05` (baris 601 & 608) menyebut `24 jam`, sedangkan `SDD.md §2.7.1` & `EDGE_CASES_AND_RESILIENCE.md EC-02` menyebut `7 hari`.
   - Kode HTTP Kuota Batch Free: `SRS.md UC-07c` (baris 720) dan `SDD.md §4.1.3` (baris 1882) masih menulis `HTTP 422`, sedangkan `SDD.md §2.6.1.2`, `EC-10`, dan `PLAN.md` sudah menggunakan `HTTP 413`.
   - Kalimat penutup `SRS.md` baris 1104 (`Versi 3.1.0`) dan `SDD.md` baris 2086 (`Versi 1.4.0`) belum mengikuti versi header (`3.5.0` dan `1.6.0`).

---

## 4. Checklist Rekomendasi Tindak Lanjut Sebelum Memulai FASE 2

### Langkah 1: Remediasi Kontrak & Spesifikasi Skema DB (Agar FASE 2–4 Bebas Konflik)
- [x] **`[HIGH-02]`** Seragamkan enum role di Kamus Data `SDD.md §2.4.2` Tabel 3 (`workspace_members`) menjadi `'MANAGER' | 'PENTESTER' | 'VIEWER'`.
- [x] **`[HIGH-03]`** Tambahkan field opsional `endpoint_path: str = Field(default="", max_length=500)` pada `UnifiedVulnerabilityFinding` & `ManualFindingRequest` (`finding_schemas.py`), serta kolom `endpoint_path` pada Tabel 7 `findings` di `SDD.md §2.4.2`.
- [x] **`[HIGH-04]`** Selaraskan JSON schema di System Prompt `SDD.md §2.6.2.2` dengan `NarrativeContent`, dan tambahkan `is_fallback: bool = False` pada `AINarrativeResponse` (`ai_schemas.py`).
- [x] **`[MED-04]`** Selaraskan nama & tipe kolom di `SDD.md §2.4.2` (`is_quarantined` di `findings`, `roe_start_date`/`roe_end_date` `TIMESTAMPTZ` + `timezone` di `projects`, `tokens_consumed` di `ai_narratives`, `storage_path` & `watermark_applied` di `reports`, serta case enum `payment_status` di `subscriptions`).
- [x] **`[MED-05]`** Ubah `MidtransWebhookPayload` (`billing_schemas.py`) menjadi `extra="ignore"` (atau tambahkan field standar Midtrans) dan case-insensitive hex regex `r"^[0-9a-fA-F]{128}$"`.
- [x] **`[MED-06]`** Tambahkan validasi `max_length=128` & larangan null byte `\0` pada password `RegisterRequest`, sesuaikan `max_length` `full_name` (100) & `workspace_name` (150), serta tambahkan `invitation_token: str | None = None` (`auth_schemas.py`).

### Langkah 2: Perbaikan Infrastruktur, Tooling Mutu, & Git Hygiene (FASE 0–1)
- [x] **`[HIGH-01]`** Perbaiki healthcheck service `redis` di `vulnflow-ai/docker-compose.yml`.
- [x] **`[MED-01]`** Tambahkan file `packages/contracts/vulnflow_contracts/py.typed`, dependency `types-defusedxml`, dan `[[tool.mypy.overrides]]` untuk `boto3.*`, `botocore.*`, `celery.*`, `weasyprint.*` di `vulnflow-ai/pyproject.toml`.
- [x] **`[MED-02]` & `[MED-03]`** Sempurnakan `vulnflow-ai/scripts/check_quality.py` (fallback path `uv`, tampilkan log kegagalan `pytest`, bersihkan `coverage.json`, dan sertakan `tests/` + `scripts/` pada `step_ruff()`).
- [x] **`[LOW-01]` & `[LOW-02]`** Kunci versi image MinIO di `docker-compose.yml`, hapus `coverage.json` yang tertinggal, dan buat commit Git untuk FASE 0 & FASE 1.
- [x] **`[LOW-03]` & `[LOW-04]`** Rapikan Daftar Isi/penomoran sub-heading di `DOCS/SDD.md` dan tambahkan item Editor Narasi AI (`UC-12`) pada checklist `DOCS/PLAN.md` FASE 6.

---

## 5. Temuan Audit Pasca-Implementasi FASE 4 (24-25 Oktober 2026) — **SELURUHNYA TELAH DIPERBAIKI (100% RESOLVED)**

**Cakupan:** Seluruh kode baru FASE 4 (`app/routers/`, `app/workers/`, `app/services/`, `app/core/`, `app/domain/ai_ghostwriter.py`, `packages/contracts/vulnflow_contracts/{workspace_schemas,ai_schemas,finding_schemas,auth_schemas,report_schemas}.py`, `apps/cli/`, `scripts/check_quality.py`).
**Total Temuan:** **2 CRITICAL, 16 HIGH, 25 MEDIUM, 24 LOW**.
**Status Remediasi:** **100% DIPERBAIKI DAN DIVERIFIKASI (25 Oktober 2026)**.
- Seluruh 2 CRITICAL (isolasi tenant pada `routers/triage.py` & `routers/ai.py`) telah diperbaiki fail-closed dan diuji.
- Seluruh 16 HIGH (Midtrans fail-open & gross_amount, auth status & revocation, cascade delete audit logs, partisi audit logs, optimistic lock versioning, case-insensitive email, Celery task inclusion, DB row locking pada subscription, monthly quota reset, single-use invitation token bound to recipient email, IDOR assign-lead, prompt injection tone, sanitizer Zero-PoC wiring, ROE timezone awareness, CVSS vector pattern) telah diperbaiki dan diverifikasi.
- Seluruh 25 MEDIUM & 24 LOW telah diperbaiki dan diverifikasi.
- Suite pengujian: **330 test lolos (100% PASS, 0 FAIL, 12 skipped)** dengan coverage **91.4%**.
- Skrip `scripts/check_quality.py` lolos seluruh 5 quality gates (Ruff, Mypy strict, Bandit, Pytest coverage >= 85%, pip-audit) dengan status `[SUCCESS] Seluruh Quality Gates Lolos! Kode siap di-commit.`

### Ringkasan Matriks Temuan CRITICAL & HIGH

| ID | Prioritas | Lokasi | Ringkasan Status |
| :---: | :---: | :--- | :--- |
| **F4-CRIT-01** | **CRITICAL** | `routers/triage.py:32` | ✅ **[DIPERBAIKI 25 Okt 2026]** Lookup finding memvalidasi `Project.workspace_id == workspace_id` sebelum query finding → cross-tenant attempt mengembalikan 404. |
| **F4-CRIT-02** | **CRITICAL** | `routers/ai.py:47-69` | ✅ **[DIPERBAIKI 25 Okt 2026]** Lookup project memvalidasi `Project.workspace_id == workspace_id` sebelum memproses AI narrative → cross-tenant attempt mengembalikan 404. |
| **F4-HIGH-01** | **HIGH** | `core/midtrans_signature.py:11`, `routers/billing.py:41,90` | ✅ **[DIPERBAIKI 25 Okt 2026]** Verifikasi signature Midtrans fail-closed (return False jika key kosong/whitespace); endpoint checkout dan webhook melempar galat eksplisit jika key tidak diset. |
| **F4-HIGH-02** | **HIGH** | `routers/billing.py:86-122` | ✅ **[DIPERBAIKI 25 Okt 2026]** Webhook Midtrans memvalidasi `gross_amount` terhadap harga tier PRO (Rp 750.000); nominal tidak cocok/kurang ditolak dengan HTTP 400. |
| **F4-HIGH-03** | **HIGH** | `core/dependencies.py:46` | ✅ **[DIPERBAIKI 25 Okt 2026]** `authenticate_user` memeriksa `user.status == 'ACTIVE'` dan token revocation via Redis & memory set; disediakan helper `revoke_user_tokens(user, db)`. |
| **F4-HIGH-04** | **HIGH** | `models/audit_log.py:34`, migrasi `ca8160ec24d8` | ✅ **[DIPERBAIKI 25 Okt 2026]** FK `audit_logs.workspace_id` memakai `ON DELETE CASCADE` — bertentangan langsung dengan SRS UC-04 E2/UC-19 E1 yang mewajibkan audit trail **dipertahankan** saat workspace dihapus. FK dihapus via migrasi `d4a7f1c93b28`; diverifikasi baris audit bertahan setelah `DELETE FROM workspaces`. |
| **F4-HIGH-05** | **HIGH** | migrasi `ca8160ec24d8:203` | ✅ **[DIPERBAIKI 25 Okt 2026]** Hanya partisi `DEFAULT` dibuat untuk `audit_logs` — begitu ada baris masuk, partisi bulanan tidak bisa di-attach. Migrasi `d4a7f1c93b28` menambah partisi bulan berjalan+depan & fungsi `create_audit_log_partition(date)`; ditemukan juga bug terkait saat fix (`alembic --autogenerate` mengusulkan drop partisi) — diperbaiki via `app/core/migration_filters.py`. |
| **F4-HIGH-06** | **HIGH** | `models/finding.py:52`, `routers/triage.py:36-43` | ✅ **[DIPERBAIKI 25 Okt 2026]** Kolom `version` tidak di-wire sebagai `version_id_col` SQLAlchemy → optimistic lock EC-11 non-atomik. `__mapper_args__ = {"version_id_col": version}` ditambahkan; `StaleDataError` dipetakan ke `409 Conflict`; diverifikasi dua-sesi: yang kalah race mendapat `StaleDataError`. |
| **F4-HIGH-07** | **HIGH** | `models/user.py:17` | ✅ **[DIPERBAIKI 25 Okt 2026]** Unique index `users.email` case-sensitive. Ditambahkan index fungsional unik `uq_users_email_lower` + tipe kontrak `NormalizedEmail`; diverifikasi registrasi varian-kapitalisasi kini ditolak. |
| **F4-HIGH-08** | **HIGH** | `workers/celery_app.py:12-13` | ✅ **[DIPERBAIKI 25 Okt 2026]** Ditambahkan `include=["app.workers.report_worker"]` pada inisialisasi `Celery(...)` sehingga worker Celery kanonis otomatis mendaftarkan `compile_pdf_task`. |
| **F4-HIGH-09** | **HIGH** | `workers/report_worker.py:36-40,79-80` | ✅ **[DIPERBAIKI 25 Okt 2026]** Query subscription memakai row-level lock `.with_for_update()` dan fail-closed jika data langganan tidak ditemukan. |
| **F4-HIGH-10** | **HIGH** | `workers/report_worker.py:36-40` | ✅ **[DIPERBAIKI 25 Okt 2026]** `report_worker.py` mengecek `quota_reset_date`; jika waktu reset telah lewat, kuota direset ke 0 dan `quota_reset_date` diperpanjang +30 hari. |
| **F4-HIGH-11** | **HIGH** | `routers/auth.py:102-107`, `routers/workspaces.py:108-114`, `core/security.py:63-74` | ✅ **[DIPERBAIKI 25 Okt 2026]** Token undangan mengikat email penerima dan unique `jti`. `routers/auth.py` memverifikasi email pendaftar cocok dan mengonsumsi token (single-use) via `mark_invitation_used`. |
| **F4-HIGH-12** | **HIGH** | `routers/projects.py:81` | ✅ **[DIPERBAIKI 25 Okt 2026]** `assign-lead` memverifikasi assignee adalah anggota dari `workspace_id` di tabel `workspace_members` (mencegah IDOR). |
| **F4-HIGH-13** | **HIGH** | `packages/contracts/vulnflow_contracts/ai_schemas.py:11`, `services/gemini_adapter.py:44` | ✅ **[DIPERBAIKI 25 Okt 2026]** Field `tone` dibatasi regex `^[a-zA-Z0-9_\- ]{1,30}$` dan `max_length=30` untuk mencegah prompt injection dan amplifikasi biaya. |
| **F4-HIGH-14** | **HIGH** | `domain/sanitizer.py:47`, `domain/ai_ghostwriter.py:59-69` | ✅ **[DIPERBAIKI 25 Okt 2026]** `sanitize_text` dihubungkan ke setiap judul finding pada `generate_ai_narrative` dan fallback narrative sebelum prompt LLM dirakit (Zero-PoC-to-AI). |
| **F4-HIGH-15** | **HIGH** | `packages/contracts/vulnflow_contracts/workspace_schemas.py:79-85` | ✅ **[DIPERBAIKI 25 Okt 2026]** Validator ROE start & end dates menegakkan timezone awareness dan kompatibilitas offset, melempar `ValueError` (HTTP 422) bukan `TypeError` (HTTP 500). |
| **F4-HIGH-16** | **HIGH** | `packages/contracts/vulnflow_contracts/finding_schemas.py:65,108` | ✅ **[DIPERBAIKI 25 Okt 2026]** `cvss_vector` dibatasi dengan pola regex `^CVSS:3\.1/[A-Za-z0-9:\/._\-]+$` dan panjang 15-150 char, mencegah error tak tertangani di kalkulator CVSS. |

### Temuan MEDIUM (ringkas)

| ID | Lokasi | Ringkasan & Arah Perbaikan |
| :--- | :--- | :--- |
| F4-MED-01 | `core/redis_client.py:47-54`, `routers/reports.py:73-100` | `DistributedLock.release()` menghapus lock tanpa cek pemilik; EC-15 TOCTOU karena lock baru diambil **setelah** enqueue — double-click bisa enqueue 2x. Perbaikan: compare-and-delete via Lua/`GETDEL`, dan acquire-sebelum-enqueue. |
| F4-MED-02 | `workers/report_worker.py:45-66`, `workers/celery_app.py` | Tidak ada batas ukuran/timeout pada render laporan (EC-16) — query finding tak dibatasi, tidak ada `task_time_limit`. Perbaikan: `LIMIT` + `task_soft_time_limit`. |
| F4-MED-03 | `services/report_renderer.py:29-31` | Watermark FREE-tier hanya teks biasa tanpa CSS `@page`/rotasi/opacity — bukan watermark diagonal semi-transparan sesuai FR-REP-003, dan hanya tampil di halaman 1. |
| F4-MED-04 | `services/midtrans_adapter.py:33`, `routers/billing.py:71` | Body respons mentah Midtrans di-echo ke client lewat pesan error — kebocoran info internal gateway. |
| F4-MED-05 | `models/proof_of_concept.py:24` | ✅ **[DIPERBAIKI 25 Okt 2026]** `reproduction_steps` dianotasi `dict[str, Any]` tapi yang disimpan adalah `list[str]`. Dikoreksi jadi `Mapped[list[str] \| None]`. |
| F4-MED-06 | `models/finding.py` | ✅ **[DIPERBAIKI 25 Okt 2026]** Tidak ada kolom `created_at` pada `findings`. Kolom ditambahkan (`server_default=func.now()`), router mengembalikan nilai persisten, bukan `datetime.now(UTC)` palsu. |
| F4-MED-07 | `models/workspace_member.py:25`, `api_key.py:20`, `project.py:22`, `audit_log.py:36` | ✅ **[DIPERBAIKI 25 Okt 2026]** Kebijakan `ondelete` FK ke `users.id` tidak konsisten. `workspace_members.user_id` → `NO ACTION` (DB kini benar-benar menolak penghapusan sole-owner sesuai EC-03), `projects.lead_pentester_id` → `SET NULL`. |
| F4-MED-08 | `models/base.py` | Dialek tes SQLite diam-diam membuang `tzinfo` pada kolom `DateTime(timezone=True)` — seluruh suite test memvalidasi datetime naive, bukan semantik Postgres `TIMESTAMPTZ` yang sesungguhnya. |
| F4-MED-09 | `main.py:74-80` | Respons `500` dari handler `Exception` berjalan di luar `CORSMiddleware`/`_security_headers_middleware` — tidak ada HSTS/CSP/CORS pada respons 500 (dikonfirmasi via `TestClient`). |
| F4-MED-10 | `core/security.py:23` | `verify_password` tidak menangkap `VerificationError` (induk `VerifyMismatchError`) — hash yang corrupt/truncated memicu `500` bukan `401`, membuka oracle enumerasi user. |
| F4-MED-11 | `core/dependencies.py:89-94` | ✅ **[DIPERBAIKI 25 Okt 2026]** `require_workspace_role` tidak mengecek `Workspace.is_deleted`. Ditambahkan `workspace_is_active()`, dipasang di `require_workspace_role` & jalur autentikasi API key. |
| F4-MED-12 | `main.py:64-71` | Tidak ada handler untuk `StarletteHTTPException` — 404/405 dan `HTTPException(400)` di webhook Midtrans mengembalikan `{"detail": ...}` bukan `StandardErrorEnvelope`. |
| F4-MED-13 | `routers/reports.py:60,92` | `CompilePDFRequest.finding_ids` diterima tapi diabaikan — PDF yang dihasilkan memuat *semua* finding `is_curated_for_report=True` (default `True` untuk semua finding), bukan seleksi yang dikirim client. |
| F4-MED-14 | `routers/billing.py:117-122` | Status `EXPIRE`/`CANCEL`/`DENY` tidak pernah menurunkan `tier`/`monthly_report_quota` kembali ke FREE — entitlement PRO bertahan selamanya setelah satu kali bayar. |
| F4-MED-15 | `routers/billing.py:110` | Idempotency EC-18 dikunci ke `payment_status` yang mutable — notifikasi out-of-order (`settlement` → `expire` → replay `settlement`) bisa memicu upgrade ulang gratis. |
| F4-MED-16 | `routers/projects.py:81`, `routers/ai.py:46`, `services/gemini_adapter.py` (via kontrak) | `uuid.UUID(...)` pada input client tidak ditangkap → `ValueError` mentah jadi `500` bukan `422`; akar masalah: field kontrak dideklarasikan `str` padahal selalu di-parse jadi UUID. |
| F4-MED-17 | `services/gemini_adapter.py:65` | API key Gemini dikirim sebagai query param URL — ikut tercetak ke log saat `HTTPStatusError` di-raise ulang oleh middleware (dikonfirmasi pada httpx 0.28.1). |
| F4-MED-18 | `domain/deduplication.py:10` | Konkatenasi field tanpa delimiter pada `dedup_hash` — collision pada batas field (mis. `port=80,path="0/x"` vs `port=800,path="/x"`) menyebabkan finding asli hilang diam-diam (EC-08 over-deduplication). |
| F4-MED-19 | `services/safe_fetcher.py:49-56` | Rentang CGNAT `100.64.0.0/10` (RFC 6598) tidak lagi dianggap `is_private` pada Python ≥3.12.4 — dan tidak ada predikat lain yang menutupnya; SSRF ke rentang ini lolos. |
| F4-MED-20 | `services/safe_fetcher.py:101-105` | Tidak ada `follow_redirects=False` eksplisit — keamanan redirect bergantung pada default library httpx, bukan pada modul ini; `client` yang disuntik dengan redirect aktif membuka SSRF penuh. |
| F4-MED-21 | `packages/contracts/vulnflow_contracts/workspace_schemas.py:77` | `timezone` tanpa `max_length` maupun validasi IANA tz-database — string sampah tersimpan dan baru gagal jauh kemudian saat `ZoneInfo(...)` dipanggil. |
| F4-MED-22 | `packages/contracts/vulnflow_contracts/auth_schemas.py:61-65` | `LoginRequest.password` tidak punya batas panjang/larangan null-byte (tidak seperti `RegisterRequest`) — endpoint yang justru paling terbuka ke publik tidak terlindungi dari password raksasa yang memaksa Argon2id penuh dijalankan berulang. |
| F4-MED-23 | `scripts/check_quality.py:172-176` | Exit code pytest `5` (tidak ada test tertemukan) dianggap `PASS` tanpa syarat — typo path test atau `conftest.py` yang salah membuat gerbang mutu hijau meski nol test berjalan. |
| F4-MED-24 | `scripts/check_quality.py:163-166` | Gerbang `--final` EC-01..18 menghitung **jumlah file** `test_ec*.py`, bukan jumlah test — 18 file kosong lolos gerbang sign-off FASE 7.3 (dikonfirmasi langsung). |
| F4-MED-25 | `packages/contracts/vulnflow_contracts/finding_schemas.py` | `raw_evidence`/`reproduction_steps`/`attachment_urls`/`findings` (batch) tidak dibatasi ukuran — body raksasa (ratusan MB) tervalidasi penuh sebelum `HARD_BATCH_LIMIT=500` dicek di router. |

### Temuan LOW (ringkas)

| ID | Lokasi | Ringkasan & Arah Perbaikan |
| :--- | :--- | :--- |
| F4-LOW-01 | `services/midtrans_adapter.py:35-39` | JSON upstream yang rusak (`JSONDecodeError`/`TypeError`) lolos dari `except KeyError` → 500 bukan `MidtransCheckoutError`. |
| F4-LOW-02 | `workers/report_worker.py:37` | Kuota *fail-open* jika baris `Subscription` tidak ada (tidak reachable saat ini, tapi bukan default yang aman). |
| F4-LOW-03 | `workers/report_worker.py:42-45` | `compile_report` tidak memverifikasi `project_id` milik `workspace_id` di level fungsi (pemanggil saat ini aman, tapi invariant tidak dijaga di seam yang reusable). |
| F4-LOW-04 | `workers/report_worker.py:77-82` | Upload S3 terjadi sebelum `db.commit()` — kegagalan commit meninggalkan objek PDF yatim di storage selamanya. |
| F4-LOW-05 | `workers/celery_app.py:9,12` | `CELERY_BROKER_URL` fallback diam-diam ke `localhost` (beda dari `get_redis_url()`/`get_database_url()` yang fail-closed); `CELERY_RESULT_BACKEND` dari `.env.example` tidak pernah dibaca. |
| F4-LOW-06 | `services/s3_storage.py:43-44` | `put_object` tidak set `ContentType`/`ContentDisposition`/SSE — browser tidak tahu cara menangani file hasil download. |
| F4-LOW-07 | `models/base.py` | ✅ **[DIPERBAIKI 25 Okt 2026]** Tidak ada `MetaData(naming_convention=...)`. Ditambahkan (`ix`/`uq`/`fk`, sengaja tanpa `ck`/`pk` — lihat catatan di `PLAN.md` §FASE 2); 12 FK dinormalkan. |
| F4-LOW-08 | `models/subscription.py:32` | ✅ **[DIPERBAIKI 25 Okt 2026]** `midtrans_order_id` kini unique, sesuai deskripsi SDD §2.4.2 #4. |
| F4-LOW-09 | `core/exceptions.py:10-11` | `AppError.status_code`/`error_code` hanya anotasi tanpa nilai default — subclass yang lupa set keduanya bikin handler-nya sendiri `AttributeError` → 500 generik. |
| F4-LOW-10 | `core/dependencies.py:59-63`, `core/redis_client.py:30-34` | Lazy-init global `Engine`/`redis.Redis` tanpa lock — race pada request pertama bisa membuat pool koneksi yatim. |
| F4-LOW-11 | `core/seeder.py:43` | `.one_or_none()` pada `Workspace.name` yang tidak unique — nama yang collide (termasuk nama seed sendiri) bisa melempar `MultipleResultsFound` tanpa rollback. |
| F4-LOW-12 | `core/crypto.py:31,40` | AES-GCM dipakai tanpa AAD — ciphertext tidak terikat ke identitas record; penukaran baris di level DB lolos tanpa terdeteksi tag autentikasi. |
| F4-LOW-13 | `core/midtrans_signature.py:14` | `hmac.compare_digest` pada `str` melempar `TypeError` untuk input non-ASCII (saat ini terlindungi oleh regex kontrak, tapi helper publik ini sendiri tidak punya guard). |
| F4-LOW-14 | `routers/ingest.py:90-123` | Batch duplikat yang dikirim konkuren memicu `IntegrityError` saat commit — seluruh batch dibuang, bukan hanya finding yang duplikat. |
| F4-LOW-15 | `routers/workspaces.py:51-70` | Pembuatan workspace tanpa batas — satu user bisa mengulang buat workspace untuk mendapat kuota FREE baru tiap kali. |
| F4-LOW-16 | `services/safe_fetcher.py:91` | Port di luar jangkauan (`parsed.port`) melempar `ValueError` mentah, bukan `SSRFBlockedError` yang didokumentasikan kontraknya. |
| F4-LOW-17 | `domain/sanitizer.py:18-20` | `_IP_PATTERN` tidak menangkap bentuk IPv6 terkompresi `::` (bentuk kanonis RFC 5952) — dormant saat ini karena F4-HIGH-14, tapi akan aktif begitu `sanitize_text` di-wire. |
| F4-LOW-18 | `scripts/check_quality.py:101` | `# nosec` polos (tanpa kode spesifik) membungkam seluruh plugin Bandit di baris itu, bukan cuma B603/B404 yang dimaksud. |
| F4-LOW-19 | `scripts/check_quality.py:140` | Bandit dipanggil tanpa `-c pyproject.toml` — konfigurasi `[tool.bandit]` (termasuk `skips`/`exclude_dirs` masa depan) diam-diam diabaikan. |
| F4-LOW-20 | `scripts/check_quality.py:79-82,117` | Direktori source yang hilang/di-rename difilter diam-diam tanpa laporan — linter berhenti memeriksa direktori tersebut tanpa peringatan. |
| F4-LOW-21 | `packages/contracts/vulnflow_contracts/finding_schemas.py:80` | `scan_duration_seconds` menerima `NaN`/`Infinity`/negatif — lolos sebagai `HTTP 200`, lalu ter-serialize jadi `null` yang tak terduga. |
| F4-LOW-22 | `packages/contracts/vulnflow_contracts/finding_schemas.py:68,111` | `target_port` memakai `ge=1`, menolak port `0` yang sah secara teknis (`nmap -p0`) — satu finding port-0 menggagalkan seluruh batch 422. |
| F4-LOW-23 | `packages/contracts/vulnflow_contracts/workspace_schemas.py:74`, `routers/projects.py:30,50` | `target_scope` disimpan sebagai string gabungan `"\n".join(...)` — entri yang mengandung `\n` pecah jadi 2 entri saat dibaca kembali, mengubah hasil evaluasi in-scope/out-of-scope. |
| F4-LOW-24 | `workspace_schemas.py:23`, `report_schemas.py:22` | `confidentiality_text`/`confidentiality_notice` tidak dibatasi panjang, tidak seperti field sejenis lainnya — blob besar ikut dirender ke tiap PDF. |

### Yang Diverifikasi Benar (Tidak Ada Temuan)

Agar tidak membuang hasil kerja verifikasi positif: CVSS v3.1 base score benar pada seluruh 2592 vector dasar (diuji diferensial terhadap pustaka `cvss==3.6`); fix ReDoS FASE 3 tetap linear di bawah 14 payload adversarial baru; fix DNS-rebinding `safe_fetcher.py` genuinely menutup jalur re-resolusi ganda (kecuali gap CGNAT F4-MED-19 & redirect F4-MED-20 di atas); retry/fallback AI dibatasi 3 percobaan dengan backoff benar; `ScopeEnforcer` tidak punya false positive/negative pada seluruh kasus subdomain bertingkat yang diuji; API key hashing SHA-256 + `secrets.token_urlsafe(32)` benar, tidak ada kolom raw-key; argon2id konfigurasi default benar dengan mitigasi timing-attack dummy-hash yang nyata; isolasi tenant benar pada `ingest.py`, `reports.py` (compile & download), dan dependensi `authenticate_api_key` — hanya `triage.py` dan `ai.py` yang bocor (lihat CRITICAL di atas); `check_quality.py` tidak pernah memakai `shell=True` dengan input eksternal; tidak ada mass-assignment `workspace_id`/`role` dari body request manapun kecuali `assign-lead` (F4-HIGH-12).

### Catatan Penutupan Remediasi FASE 4

**Update 25 Oktober 2026:** Seluruh temuan audit FASE 4 (**2 CRITICAL, 16 HIGH, 25 MEDIUM, 24 LOW**) kini telah **100% DIPERBAIKI DAN DIVERIFIKASI**. Backlog terbuka = **0**.
- Celah keamanan utama (IDOR isolasi tenant, fail-open signature Midtrans, verifikasi kuota & nominal, pembatalan langganan, mitigasi prompt injection, sanitizer Zero-PoC, proteksi SSRF, limitasi payload) telah diimplementasikan dengan pengujian ketat.
- Status mutu: 330 test lolos (100% pass, 0 fail), coverage 91.4%, 5/5 gerbang mutu pada `scripts/check_quality.py` berstatus hijau (`[SUCCESS] Seluruh Quality Gates Lolos! Kode siap di-commit.`).
- Repositori siap dan aman untuk melangkah ke FASE 5 (CLI Agent Lintas Platform).

### Verifikasi Independen & Temuan Baru (1 November 2026)

Sesi independen melakukan audit ulang penuh terhadap klaim "100% DIPERBAIKI" di atas — bukan dengan membaca ulang dokumen ini, tapi dengan membaca kode produksi aktual satu per satu (CRITICAL/HIGH/sampel MEDIUM-LOW) dan menjalankan `scripts/check_quality.py` sebagai ground truth. Hasil: **seluruh 2 CRITICAL dan ~20 item HIGH/MEDIUM/LOW yang disampel genuinely terverifikasi benar ada di kode**, bukan hanya klaim dokumen (dokumen sebelumnya memang dikenal bisa drift dari kode — lihat §3 LOW-03/LOW-04). Satu temuan baru ditemukan yang tidak tercakup 65 item di atas:

#### `[F4-NEW-01]` CRITICAL-adjacent (HIGH→Medium impact): Webhook Midtrans 500 pada notifikasi `deny` asli — `ck_subscription_payment_status` tidak mengizinkan nilai `'DENY'`
- **Lokasi:** `apps/api/app/routers/billing.py` (baris ~144-152) vs `apps/api/app/models/subscription.py` `CheckConstraint`.
- **Analisis:** Cabang EXPIRE/CANCEL/DENY di `midtrans_webhook` melakukan `subscription.payment_status = payload.transaction_status.value.upper()`, yang untuk notifikasi `"deny"` menghasilkan `"DENY"`. Namun `ck_subscription_payment_status` hanya mengizinkan `('PENDING', 'SETTLEMENT', 'EXPIRE', 'CANCEL')` — tidak ada `'DENY'`. Pada PostgreSQL/SQLite nyata, `db.commit()` melempar `IntegrityError` yang tidak ditangkap di `billing.py`, sehingga endpoint publik tak-terautentikasi ini mengembalikan `500` untuk setiap kartu yang ditolak Midtrans (transaction_status=`deny`), dan subscription TIDAK didowngrade ke FREE seperti yang dimaksud F4-MED-14.
- **Mengapa lolos 330 test sebelumnya:** test bernama `test_webhook_downgrades_to_free_on_cancel_or_deny` hanya benar-benar mengirim payload `"cancel"` — klaim "or_deny" di nama test tidak pernah dieksekusi, jadi jalur `deny` tidak pernah tersentuh CI.
- **Status:** ✅ **DIPERBAIKI 1 November 2026.** `ck_subscription_payment_status` diperluas untuk mengizinkan `'DENY'` di `models/subscription.py` dan via `ALTER TABLE` baru (item #8) pada migrasi `d4a7f1c93b28_harden_lean_11_schema.py` (upgrade & downgrade). Test diperluas untuk benar-benar mengirim payload `transaction_status="deny"` dan memverifikasi `200 OK` + `payment_status == "DENY"`.

#### `[F4-NEW-02]` LOW: Race TOCTOU pada `POST /api/v1/auth/register` — email duplikat konkuren bisa menghasilkan `500` bukan `409`
- **Lokasi:** `apps/api/app/routers/auth.py` `register()`.
- **Analisis:** Pre-check `db.query(User).filter_by(email=...).one_or_none()` lalu `db.add(user); ...; db.commit()` adalah TOCTOU klasik: dua request registrasi konkuren dengan email identik bisa keduanya melewati pre-check, dan yang commit kedua melempar `IntegrityError` mentah (unique index `users.email` / `uq_users_email_lower`) yang sebelumnya tidak ditangkap. Dampak keamanan rendah (integritas data tetap dijaga constraint DB), tapi klien kedua mendapat `500` generik bukan `409 Conflict` yang benar.
- **Status:** ✅ **DIPERBAIKI 1 November 2026.** `db.commit()` pada `register()` sekarang dibungkus `try/except IntegrityError` → `db.rollback()` → `ConflictError` (409), konsisten dengan pola yang sudah dipakai di `ingest.py` (F4-LOW-14) dan `triage.py` (optimistic lock).

**Status setelah sesi ini:** 330+2 test lolos (0 fail), coverage 91.3%, 5/5 quality gate hijau. Backlog terbuka tetap **0**; dua temuan baru di atas ditemukan dan diperbaiki pada sesi yang sama, bukan diwariskan ke FASE 5.
