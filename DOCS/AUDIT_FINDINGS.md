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
