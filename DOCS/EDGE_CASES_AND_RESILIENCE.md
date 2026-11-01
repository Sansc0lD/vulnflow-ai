# MATRIKS KASUS BATAS, KETAHANAN SISTEM & RENCANA PENGUJIAN
## (SYSTEM RESILIENCE, EDGE CASES MITIGATION & QA TEST PLAN)

**Platform:** VulnFlow AI (SaaS Vulnerability Management & Reporting Assistant)  
**Dokumen Induk:** [Software Requirements Specification (SRS) v3.5.0](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/SRS.md) & [Software Design Description (SDD) v1.6.0](file:///c:/Users/KaliCodeS3/Documents/Project/IPPL/DOCS/SDD.md)  
**Standar Acuan:** IEEE Std 1016:2009 (Software Design), ISO/IEC 25010:2023 (Fault Tolerance & Reliability), ISO/IEC/IEEE 29119 (Software Testing)  
**Status Dokumen:** **Resmi & Mengikat Implementasi Kode (Single Source of Truth for QA & Robustness)**

---

## 1. Pendahuluan & Filosofi Perancangan Sistem (*Defensive Engineering*)

Tujuan utama dari dokumen ini adalah menjamin bahwa platform **VulnFlow AI** tidak memiliki celah logika, ambiguitas perilaku, atau titik kegagalan tunggal (*single point of failure*) yang dapat menghentikan atau merusak pengalaman kerja pengguna (*user workflow*).

Sistem dirancang mengacu pada 4 prinsip utama ketahanan perangkat lunak:
1. **Frictionless User Experience (UX):** Pengguna tidak boleh dibiarkan menghadapi kondisi buntu (*dead-end*). Jika terjadi kegagalan eksternal, sistem wajib menyediakan alternatif (*fallback*) atau degradasi anggun (*graceful degradation*).
2. **Zero Data Loss Policy:** Kegagalan transient jaringan, kedaluwarsa sesi langganan, atau interupsi proses tidak boleh mengakibatkan hilangnya data proyek, temuan, bukti PoC, atau laporan audit yang telah dihasilkan.
3. **Idempotent Operations:** Seluruh operasi yang berpotensi ditransmisikan ulang (seperti webhook pembayaran Midtrans dan pengunggahan berkas batch CLI) wajib bersifat idempoten untuk mencegah anomali data ganda.
4. **Strict Architectural Isolation:** Pemisahan tegas antara tugas pemindaian lokal (di mesin pengguna) dengan mesin agregasi pelaporan di cloud SaaS, guna melindungi batas hukum dan keamanan jaringan.

---

## 2. Arsitektur Biner Lintas Platform CLI (*Cross-Platform Provisioning*)

### 2.1 Masalah & Kebutuhan Pengguna
Pengguna platform VulnFlow AI menggunakan beragam sistem operasi (Windows 10/11, macOS Intel & Apple Silicon M-series, serta berbagai distribusi Linux). Banyak pengguna pemula atau auditor di workstation korporat tidak memiliki tools scanner (Nmap atau Nuclei) terpasang di sistem mereka.

### 2.2 Mekanisme Deteksi & Pengunduhan Otomatis (`vulnflow setup-tools`)
CLI Agent (`apps/cli`) dibangun dengan Python 3.10+ murni dan memanfaatkan pustaka bawaan `platform` untuk mendeteksi lingkungan eksekusi secara deterministik tanpa dependensi eksternal:

```python
import platform
import os
import stat
import urllib.request
import zipfile
import tarfile
from pathlib import Path


def resolve_target_environment() -> dict:
    os_raw = platform.system().lower()
    arch_raw = platform.machine().lower()

    # Normalisasi Sistem Operasi
    if "windows" in os_raw:
        os_tag = "windows"
        ext = ".zip"
        binary_name = "nuclei.exe"
    elif "darwin" in os_raw:
        os_tag = "macOS"
        ext = ".zip"
        binary_name = "nuclei"
    else:
        os_tag = "linux"
        ext = ".zip"
        binary_name = "nuclei"

    # Normalisasi Arsitektur CPU
    if arch_raw in ["amd64", "x86_64"]:
        arch_tag = "amd64"
    elif arch_raw in ["arm64", "aarch64"]:
        arch_tag = "arm64"
    else:
        arch_tag = "386"

    return {
        "os": os_tag,
        "arch": arch_tag,
        "extension": ext,
        "binary_name": binary_name,
        "download_url": f"https://github.com/projectdiscovery/nuclei/releases/latest/download/nuclei_{os_tag}_{arch_tag}{ext}",
    }


def ensure_tools_installed() -> Path:
    install_dir = Path.home() / ".vulnflow" / "bin"
    install_dir.mkdir(parents=True, exist_ok=True)
    env_info = resolve_target_environment()
    target_binary = install_dir / env_info["binary_name"]

    if not target_binary.exists():
        archive_path = install_dir / f"nuclei_temp{env_info['extension']}"
        urllib.request.urlretrieve(env_info["download_url"], archive_path)
        with zipfile.ZipFile(archive_path, "r") as zip_ref:
            zip_ref.extract(env_info["binary_name"], install_dir)
        archive_path.unlink()

        # Pasang izin eksekusi (chmod +x) pada Linux/macOS
        if env_info["os"] != "windows":
            st = os.stat(target_binary)
            os.chmod(target_binary, st.st_mode | stat.S_IEXEC)

    return target_binary
```

> **Catatan implementasi FASE 5.3:** Snippet di atas ilustratif — `urllib.request.urlretrieve(...)` dan `zip_ref.extract(...)` tanpa validasi memicu **Bandit B310** (unverified URL scheme) dan **B202** (tarfile/zip extraction tanpa cek path traversal). Implementasi nyata wajib memakai `httpx` (konsisten dengan dependensi CLI lain) untuk unduhan, dan memvalidasi setiap anggota arsip (`zip_ref.namelist()`) tidak keluar dari `install_dir` sebelum ekstraksi.

### 2.3 Penanganan Izin Administrator (Nmap Raw Sockets)
Jika pengguna menjalankan scanner porta (Nmap) yang membutuhkan hak akses raw socket untuk SYN scan (`-sS`):
- CLI Agent menangkap status return code Nmap.
- Jika return code mengindikasikan pelanggaran izin (`Permission denied` / `WSAEACCES`), CLI menampilkan pesan instruksi human-readable:
  - **Windows:** *"Nmap memerlukan hak akses Administrator untuk raw sockets. Buka PowerShell / Terminal dengan opsi 'Run as Administrator'"*.
  - **Linux / macOS:** *"Jalankan perintah dengan prefix `sudo` untuk mengizinkan pembuatan paket TCP mentah"*.

---

## 3. Tata Kelola Hukum & Batasan Otorisasi Target (*Rules of Engagement - ROE*)

### 3.1 Pencegahan Aktivitas Pemindaian Ilegal (*Legal Liability Shield*)
Dalam etika pengujian penetrasi profesional, pemindaian terhadap aset tanpa izin pemilik adalah tindak pidana siber. VulnFlow AI menerapkan perlindungan berlapis:
1. **Click-Wrap Legal Attestation (Wajib):** Saat pembuatan proyek (`UC-06`), pengguna wajib mencentang klausul hukum:  
   *"Saya menyatakan secara sadar bahwa saya memiliki izin tertulis resmi (Rules of Engagement) dari pemilik aset yang sah untuk mengaudit target yang didaftarkan. Segala aktivitas di luar izin menjadi tanggung jawab hukum saya pribadi."*
2. **Definisi Jangka Waktu ROE (`roe_start_date` s.d. `roe_end_date`):** Sistem memvalidasi apakah pengunggahan log temuan berada dalam rentang waktu kontrak yang legal.
3. **Penyimpanan Dokumen Kontrak:** Pengguna dapat mengunggah berkas NDA / Surat Tugas bertanda tangan digital (PDF) sebagai lampiran resmi proyek.

### 3.2 Verifikasi Kepemilikan Domain untuk Pemindaian Cloud (*Domain Ownership Verification*)
Jika pengguna menginisiasi pemindaian langsung dari dashboard web (fitur *Web Quick Scan*):
- **Metode A (DNS TXT Challenge):** Sistem menghasilkan token unik acak, misal `vulnflow-verification=vfv_9a8b7c6d`. Klien memasang DNS TXT record pada `_vulnflow.targetapp.com`. Backend melakukan DNS lookup untuk memvalidasi kepemilikan.
- **Metode B (HTTP Well-Known Token):** Klien menaruh berkas teks pada `https://targetapp.com/.well-known/vulnflow-token.txt`. Backend melakukan HTTP GET sederhana untuk mencocokkan token.

### 3.3 Penegakan Batasan Target Otomatis (*Out-of-Scope Quarantine - UC-07d*)
Backend secara otomatis memeriksa setiap temuan yang diunggah terhadap daftar `target_scope` proyek:
- Jika target temuan berada di luar scope izin (misal auditor memindai subnet pihak ketiga), temuan otomatis diberi tanda `is_quarantined = true` dan **ditolak masuk ke dalam laporan klien**, menjaga agensi pentesting dari tuntutan hukum pelanggaran batas audit.

---

## 4. Matriks Komprehensif 18 Kasus Batas (Edge Cases EC-01 s.d. EC-18)

| ID Kasus | Fase Alur Kerja | Skenario Kasus Batas (*Trigger*) | Dampak Potensial pada Pengguna | Solusi Teknis & Mitigasi Arsitektur | Kode Status HTTP / Mekanisme |
| :---: | :--- | :--- | :--- | :--- | :---: |
| **EC-01** | Multi-Tenancy | Auditor tergabung dalam banyak workspace | Temuan salah kirim ke workspace agensi lain | CLI membaca `active_workspace_id` di `config.json` lokal | Validasi Client-Side & `403 Forbidden` |
| **EC-02** | Multi-Tenancy | Undangan anggota ke email yang belum terdaftar | Alur kolaborasi terhambat | Sistem menerbitkan signed `invitation_token` (JWT 7 hari) | Auto-join saat registrasi |
| **EC-03** | Multi-Tenancy | Owner tunggal menghapus akun saat proyek aktif | Workspace dan proyek menjadi yatim (*orphaned*) | Larangan hapus akun sebelum *Transfer Ownership* | `HTTP 409 Conflict` |
| **EC-04** | Scoping & ROE | Host target berupa subdomain bertingkat | Hasil scan salah dianggap *Out-of-Scope* | Normalisasi FQDN & Regex Suffix Tree di `ScopeEnforcer` | Normalisasi Pra-Pencocokan |
| **EC-05** | Scoping & ROE | Perbedaan zona waktu pada tanggal kedaluwarsa ROE | Audit ditutup prematur (selisih jam server UTC) | Simpan `TIMESTAMPTZ` & simpan atribut `timezone` proyek | Evaluasi Waktu Berbasis Proyek |
| **EC-06** | CLI Ingestion | Pemindaian scanner terpotong paksa (`Ctrl+C`) | Berkas JSON korup, gagal diunggah seluruhnya | Parser membaca *JSON Lines (JSONL / NDJSON)* baris per baris | Streaming Parser `try...except` |
| **EC-07** | CLI Ingestion | Jaringan terputus saat upload muatan batch besar/terpecah (*chunked*) | Unggahan gagal, temuan terduplikasi, atau fragmen senyap tidak tersimpan | HTTPX auto-retry 3x backoff & `Idempotency-Key` per-fragmen (`file_hash:chunk_index`, lihat §5.5); jaring pengaman data: `dedup_hash` per-temuan (EC-08) | Idempotent Chunked Ingestion Pipeline |
| **EC-08** | Ingestion DB | Rumus hash deduplikasi mengabaikan path URL | Celah sama di URL berbeda terhapus | $\text{dedup\_hash} = \text{SHA256}(\dots + \text{endpoint\_path})$ | Pencegahan Over-deduplication |
| **EC-09** | Ingestion DB | Celah non-jaringan tidak memiliki porta (`null`) | Crash konversi tipe data atau UI error | Field `target_port` nullable, fallback render `"N/A"` | Validasi Skema Pydantic V2 |
| **EC-10** | Ingestion DB | Batch scan menghasilkan 52 temuan pada akun Free | Pengguna buntu karena kuota Free maksimal 50 | *Graceful degradation:* CLI tawarkan upload 50 teratas | `HTTP 413` + CLI User Prompt |
| **EC-11** | Triage & Edit | Dua auditor menyunting temuan secara bersamaan | Kerja auditor saling menimpa (*race condition*) | *Optimistic Locking* dengan kolom `version` (INTEGER) | `HTTP 409 Conflict` |
| **EC-12** | Triage & Export | Temuan `FALSE_POSITIVE` tercentang ke laporan | Dokumen laporan memuat data palsu | Backend otomatis set `is_curated_for_report = false` | Aturan Bisnis Domain Service |
| **EC-13** | AI Generator | Server target memuat banner instruksi jahat | *Indirect prompt injection* memanipulasi AI | Sanitasi ketat teks & pemisahan `system_instruction` | Sanitizer Regex & Gemini Guard |
| **EC-14** | AI Generator | Kuota API LLM habis (`HTTP 429`) / jaringan timeout | Proses pembuatan laporan terhenti total | **Deterministic In-Memory Fallback Engine** (`cwe_catalog.json`) | Fallback In-Memory $\mathcal{O}(1) < 1\text{ ms}$ |
| **EC-15** | PDF Generator | Pengguna mengklik tombol "Export PDF" berkali-kali | Kuota bulanan tersedot ganda | *Distributed Lock* Redis (`lock:report:{id}`) 10 detik | `HTTP 202` (Return Job Sama) |
| **EC-16** | PDF Generator | Worker WeasyPrint kehabisan memori (*PDF Bomb*) | Progress bar web membeku selamanya | Celery `on_failure` refund kuota & set status `FAILED` | Kompensasi Transaksi Kuota |
| **EC-17** | PDF Generator | Tautan download S3 kedaluwarsa setelah 15 menit | Pengguna mendapat error 403 Access Denied | Endpoint proxy me-redirect ke presigned URL baru | `HTTP 307 Temporary Redirect` |
| **EC-18** | Midtrans | Server Midtrans mengirim webhook callback ganda | Kuota laporan bertambah lebih dari haknya | Handler memeriksa `subscriptions.payment_status == 'SETTLEMENT'` | Webhook Idempotency Check |

---

## 5. Rincian Teknis & Implementasi Mitigasi Kasus Batas

### 5.1 Penanganan Kasus EC-06: Parser Streaming JSON Lines (JSONL)
```python
# apps/cli/parsers/nuclei_parser.py
import json
from typing import Generator


def parse_nuclei_stream(file_path: str) -> Generator[dict, None, None]:
    """
    Mendukung berkas JSON utuh maupun format JSON Lines (NDJSON) yang terpotong.
    Menjamin temuan yang sudah selesai dipindai sebelum crash tetap terselamatkan.
    """
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        # Coba muat sebagai array JSON utuh terlebih dahulu
        content = f.read().strip()
        if content.startswith("[") and content.endswith("]"):
            try:
                data = json.loads(content)
                for item in data:
                    yield item
                return
            except json.JSONDecodeError:
                pass  # Lanjutkan ke fallback streaming baris per baris

        # Fallback: Streaming baris per baris (JSONL / Interrupted File)
        f.seek(0)
        for line_num, line in enumerate(f, 1):
            line_str = line.strip()
            if not line_str or line_str in ["[", "]", ","]:
                continue
            if line_str.endswith(","):
                line_str = line_str[:-1]
            try:
                yield json.loads(line_str)
            except json.JSONDecodeError:
                continue  # Lewati baris yang korup di ujung berkas
```

### 5.2 Penanganan Kasus EC-08: Formula Hash Deduplikasi Presisi
```python
# apps/api/domain/deduplication.py
import hashlib


def compute_dedup_hash(
    project_id: str, cwe_id: str, host: str, port: int | None, path: str = ""
) -> str:
    """
    Menghasilkan hash deterministik unik per endpoint celah.
    Mencegah bug over-deduplication jika celah sama ada di dua path berbeda.
    """
    normalized_port = str(port) if port is not None else "no-port"
    normalized_path = path.strip().lower()
    raw_key = f"{project_id}:{cwe_id.upper()}:{host.lower()}:{normalized_port}:{normalized_path}"
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
```

### 5.3 Penanganan Kasus EC-15 & EC-16: Distributed Lock & Kompensasi Kuota
```python
# apps/api/routers/reports.py
from fastapi import APIRouter, HTTPException, status
from redis import Redis

router = APIRouter()


@router.post(
    "/workspaces/{w_id}/projects/{p_id}/reports/compile-pdf", status_code=status.HTTP_202_ACCEPTED
)
def compile_pdf(w_id: str, p_id: str, redis: Redis, db_session):
    lock_key = f"lock:report:{w_id}:{p_id}"
    # Dapatkan lock terdistribusi 10 detik untuk mencegah race condition double click
    acquired = redis.set(lock_key, "LOCKED", nx=True, ex=10)
    if not acquired:
        existing_job_id = redis.get(f"active_job:{w_id}:{p_id}")
        if existing_job_id:
            return {
                "job_id": existing_job_id.decode(),
                "status": "QUEUED",
                "message": "Pekerjaan sedang berjalan",
                "status_url": f"/api/v1/workspaces/{w_id}/reports/jobs/{existing_job_id.decode()}",
            }
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Permintaan kompilasi sedang diproses",
        )

    # Validasi dan inkrementasi kuota
    sub = db_session.query(Subscription).filter_by(workspace_id=w_id).with_for_update().first()
    if sub.reports_used_this_month >= sub.monthly_report_quota:
        redis.delete(lock_key)
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="Kuota laporan bulanan telah habis"
        )

    sub.reports_used_this_month += 1
    db_session.commit()

    # Enqueue Celery task
    task = render_pdf_task.delay(w_id, p_id)
    redis.set(f"active_job:{w_id}:{p_id}", task.id, ex=300)
    return {
        "job_id": task.id,
        "status": "QUEUED",
        "message": "Permintaan kompilasi PDF telah masuk dalam antrean latar belakang Celery.",
        "status_url": f"/api/v1/workspaces/{w_id}/reports/jobs/{task.id}",
    }
```

```python
# apps/api/workers/report_tasks.py
@celery_app.task(bind=True)
def render_pdf_task(self, w_id: str, p_id: str):
    try:
        # Jalankan WeasyPrint compilation...
        pdf_bytes = execute_weasyprint(p_id)
        upload_to_s3(pdf_bytes)
    except Exception as exc:
        # EC-16: Rollback kuota jika terjadi crash / Out-Of-Memory
        with get_db_session() as session:
            sub = session.query(Subscription).filter_by(workspace_id=w_id).with_for_update().first()
            if sub and sub.reports_used_this_month > 0:
                sub.reports_used_this_month -= 1
                session.commit()
        raise self.retry(exc=exc, max_retries=1)
```

### 5.4 Penanganan Kasus EC-17: Regenerasi Tautan Presigned URL Otomatis
```python
# apps/api/routers/reports.py
@router.get("/workspaces/{w_id}/reports/{report_id}/download")
def download_report_proxy(w_id: str, report_id: str, current_user, s3_client, db_session):
    report = db_session.query(Report).filter_by(id=report_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Laporan tidak ditemukan")

    # Terbitkan presigned URL segar yang berlaku 15 menit
    fresh_presigned_url = s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": "vulnflow-reports", "Key": report.storage_path},
        ExpiresIn=900,
    )
    # Redirect otomatis browser pengguna ke URL segar
    return RedirectResponse(url=fresh_presigned_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
```

### 5.5 Penanganan Kasus EC-07: Granularitas `Idempotency-Key` pada Chunked Streaming
Untuk berkas pemindaian raksasa (> 200 MB) yang dipecah CLI menjadi beberapa fragmen (EC-06/UC-07 E3), kunci idempotensi **tidak boleh** berupa satu hash file tunggal yang diulang di setiap fragmen — jika demikian, backend akan memperlakukan fragmen ke-2 dan seterusnya sebagai *replay* dari fragmen pertama dan mengabaikannya secara senyap (*silent data loss*, tanpa galat yang terlihat CLI maupun pentester). Kunci idempotensi harus **unik per fragmen**, namun **stabil lintas percobaan ulang (retry)** fragmen yang sama:

```python
# apps/cli/services/ingest_client.py
import hashlib


def compute_idempotency_key(file_hash: str, chunk_index: int | None = None) -> str:
    """
    Payload tunggal (tidak di-chunk): kunci = hash file.
    Payload ter-chunk: kunci = hash file + indeks fragmen, sehingga:
      - Fragmen berbeda -> kunci berbeda -> tidak saling menimpa/di-skip.
      - Fragmen yang sama diulang (retry jaringan) -> kunci identik -> tetap idempoten.
    """
    if chunk_index is None:
        return file_hash
    return f"{file_hash}:{chunk_index}"
```

```python
# apps/api/routers/ingest.py
# Backend memperlakukan Idempotency-Key sebagai gerbang PER REQUEST HTTP (bukan per file):
# cukup untuk mencegah 1 fragmen diproses dua kali, TIDAK dimaksudkan sebagai mekanisme
# deduplikasi data lintas-fragmen. Deduplikasi data yang sesungguhnya tetap bertumpu pada
# dedup_hash per-temuan (EC-08), yang dihitung ulang dari isi temuan itu sendiri dan karena
# itu valid apakah temuan tiba dalam 1 request besar atau tersebar di N fragmen kecil.
```

---

## 6. Panduan Implementasi Pengujian Otomatis (*Pytest QA Test Plan*)

Seluruh 18 kasus batas ini wajib memiliki uji otomatis (*automated test suite*) pada direktori `tests/test_resilience/`. Daftar di bawah ini adalah daftar **kanonik** — PLAN.md FASE 7.2 wajib selalu mencerminkan 18 nama file yang persis sama:

1. `tests/test_resilience/test_ec01_multi_workspace_context.py` (EC-01: CLI salah kirim temuan ke workspace lain).
2. `tests/test_resilience/test_ec02_invitation_token_expiry.py` (EC-02: klaim undangan setelah token 7 hari kedaluwarsa).
3. `tests/test_resilience/test_ec03_orphan_workspace_prevention.py` (EC-03: owner tunggal mencoba hapus akun saat proyek masih aktif).
4. `tests/test_resilience/test_ec04_scope_enforcement_cidr.py` (EC-04: normalisasi FQDN/CIDR pada subdomain bertingkat).
5. `tests/test_resilience/test_ec05_roe_timezone_boundary.py` (EC-05: evaluasi kedaluwarsa ROE lintas zona waktu).
6. `tests/test_resilience/test_ec06_cli_interrupted_jsonl.py` (EC-06: berkas JSONL terpotong akibat `Ctrl+C`).
7. `tests/test_resilience/test_ec07_chunked_ingest_idempotency.py` (EC-07: kirim 3 fragmen berbeda dengan `file_hash` sama namun `chunk_index` berbeda → seluruh fragmen tersimpan; kirim ulang fragmen ke-2 dengan kunci identik → tidak terjadi duplikasi pada fragmen tersebut).
8. `tests/test_resilience/test_ec08_dedup_hash_path_differentiation.py` (EC-08: dua temuan sama persis kecuali path endpoint tidak boleh ter-dedup).
9. `tests/test_resilience/test_ec09_nullable_port_rendering.py` (EC-09: temuan tanpa porta tidak boleh membuat parser/UI crash).
10. `tests/test_resilience/test_ec10_free_tier_graceful_prompt.py` (EC-10: batch 52 temuan pada akun Free direspons `HTTP 413` + prompt interaktif CLI).
11. `tests/test_resilience/test_ec11_triage_optimistic_locking.py` (EC-11: 2 request konkuren mengubah status temuan yang sama).
12. `tests/test_resilience/test_ec12_false_positive_report_exclusion.py` (EC-12: temuan `FALSE_POSITIVE` otomatis di-uncheck dari kurasi laporan).
13. `tests/test_resilience/test_ec13_prompt_injection_sanitization.py` (EC-13: banner target berisi instruksi adversarial ke AI).
14. `tests/test_resilience/test_ec14_ai_in_memory_fallback.py` (EC-14: kuota/timeout LLM memicu fallback katalog CWE lokal).
15. `tests/test_resilience/test_ec15_pdf_distributed_lock_double_click.py` (EC-15: klik ganda tombol Export PDF saat sisa kuota 1).
16. `tests/test_resilience/test_ec16_report_worker_crash_quota_rollback.py` (EC-16: worker WeasyPrint crash → kuota harus di-refund).
17. `tests/test_resilience/test_ec17_presigned_url_dynamic_regeneration.py` (EC-17: presigned URL S3 kedaluwarsa, regenerasi via `HTTP 307`).
18. `tests/test_resilience/test_ec18_midtrans_webhook_idempotency.py` (EC-18: 3 request webhook Midtrans identik hanya memproses kuota sekali).

---
*Dokumen ini menjadi rujukan resmi jaminan keandalan sistem VulnFlow AI — 2026.*
