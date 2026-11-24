# Panduan Testing Organik di Browser (End-to-End Semua Role) — VulnFlow AI

Dokumen ini memandu pengujian manual secara organik di browser — mulai dari menyalakan seluruh server lokal sampai menguji semua peran pengguna: **Public Visitor**, **Manager**, **Pentester**, **Viewer**, dan **Superadmin**.

> Seluruh label tombol/menu di panduan ini mengacu pada teks UI aktual di `apps/web` (berbahasa Inggris).

---

## Tahap 0 — Menyalakan Seluruh Server & Infrastruktur

### Prasyarat
- **Docker Desktop** sudah menyala.
- File `.env` sudah ada di root repositori (minimal memiliki `POSTGRES_PASSWORD`, `REDIS_PASSWORD`, `JWT_SECRET_KEY`, `ENCRYPTION_MASTER_KEY`, `SEED_ADMIN_PASSWORD`, `SEED_ADMIN_TOTP_SECRET`, serta `GEMINI_API_KEY` dan `MIDTRANS_SERVER_KEY` jika ingin mengetes AI & Billing live).
- Dependensi workspace Python (`uv sync --all-packages`) dan frontend (`pnpm --dir apps/web install`) sudah terpasang.

### Langkah 1 — Nyalakan 6 Container Backend & Infrastruktur
Jalankan dari root folder proyek (`vulnflow-ai/`):

```powershell
docker compose up -d --build
docker compose ps
```

Pastikan keenam service aktif:
- `vulnflow-postgres` (`healthy`)
- `vulnflow-redis` (`healthy`)
- `vulnflow-minio` (`healthy`)
- `vulnflow-mailpit` (`healthy`)
- `vulnflow-api` (`healthy`)
- `vulnflow-worker` (`Up`)

Cek healthcheck API:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
# Expected: status = ok
```

### Langkah 2 — Pastikan Akun Superadmin & Template Ter-seed
> Jika `vulnflow-api` baru pertama kali dijalankan atau database baru di-reset, pastikan seeder sudah berjalan:

```powershell
docker compose exec -T api python -c "from app.core.database import make_engine, make_session_factory, get_database_url; from app.core.seeder import seed_defaults; s = make_session_factory(make_engine(get_database_url()))(); seed_defaults(s)"
```

Seeder ini membuat:
- Akun Superadmin: `admin@vulnflow.local` (password mengikuti `SEED_ADMIN_PASSWORD` di `.env`, default `.env.example`: `VulnFlow-Seed-Admin-2026!`)
- Workspace template internal Free (`quota = 3`) & Pro (`quota = 30`)

### Langkah 3 — Nyalakan Frontend Web SPA (`http://localhost:5173`)
Buka terminal terpisah (biarkan tetap berjalan selama pengujian):

```powershell
pnpm --dir apps/web run dev
```

Tunggu hingga muncul `Local: http://localhost:5173/`.

### Daftar URL Lokal Selama Pengujian

| Layanan | URL | Kegunaan |
|:--- |:--- |:--- |
| **Web App (Frontend SPA)** | http://localhost:5173 | UI utama (rute publik & `/app/*`) |
| **Mailpit (Email Sandbox)** | http://localhost:8025 | Melihat email undangan & reset password |
| **Swagger API Docs** | http://127.0.0.1:8000/docs | Referensi & cek endpoint FastAPI |
| **MinIO Console** | http://localhost:9001 | Melihat bucket logo agency, screenshot PoC, dan PDF |

### Tips Pengujian Multi-Role di Browser
Karena autentikasi menggunakan `localStorage` per origin, gunakan trik berikut agar tidak perlu terus-menerus login ulang:
- **Browser Utama:** Login sebagai **`MANAGER`**
- **Window Incognito / Private (atau Profil Browser ke-2):** Bergantian untuk **`PENTESTER`**, **`VIEWER`**, dan **`SUPERADMIN`** (atau klik `Sign out` di pojok kiri bawah sidebar setiap berpindah akun).

---

## Ringkasan Matriks Hak Akses (RBAC) di Browser

| Fitur / Halaman | Public | `VIEWER` | `PENTESTER` | `MANAGER` | `SUPERADMIN` |
|:--- |:---:|:---:|:---:|:---:|:---:|
| Rute Publik (`/`, `/about`, `/solutions`, `/solutions/:id`, `/contact`, `/verify/:code?`) | Ya | Ya | Ya | Ya | Ya |
| `/app/dashboard` (`Overview`) | - | Read | Read | Read | Redirect `/app/admin` |
| `/app/projects` (`New project` & `Edit`) | - | Read | Create/Edit | Create/Edit + `Project Lead` | Redirect `/app/admin` |
| `/app/triage`: tambah temuan / ubah status / kurasi | - | Read-only | Ya | Ya | Redirect `/app/admin` |
| `/app/triage`: `Approve into scope` (un-quarantine) | - | Tidak | Tidak | **Ya** | - |
| `/app/triage`: lihat PoC mentah terdekripsi & upload screenshot | - | **Diblokir** | **Ya** | **Ya** | - |
| `/app/ai-review`: `Generate Draft`, `Edit`, `Save Draft`, `Approve Draft` | - | Read-only | **Ya** | **Ya** | Redirect `/app/admin` |
| `/app/theme`: ubah warna/logo/NDA (`Save branding`, `Upload logo`) | - | Read-only | Read-only | **Ya** | Redirect `/app/admin` |
| `/app/theme`: `Export PDF Report` & `Download PDF` | - | `Download PDF` saja | Ya | Ya | - |
| `/app/billing`: lihat kuota & klik `Upgrade to Pro` | - | Lihat saja | Lihat saja | **Ya** | Redirect `/app/admin` |
| `/app/settings`: `Team & Workspaces` (Invite, Role, Hapus) | - | Join/Create WS | Join/Create WS | **Ya (penuh)** | Disembunyikan |
| `/app/settings`: `CLI API Keys` | - | Diblokir | **Ya** | **Ya** | Disembunyikan |
| `/app/settings`: `Activity Log` Workspace | - | Diblokir | Diblokir | **Ya** | Disembunyikan |
| `/app/settings`: `Account Security` (2FA TOTP) | - | Ya | Ya | Ya | **Ya (Security-only)** |
| `/app/admin` (`AI Usage`, `Users`, `Workspaces & Plans`, `Audit Logs`) | - | Ditolak | Ditolak | Ditolak | **Ya** |

---

## Skenario 1 — Public Visitor (Tanpa Login)

Uji 6 halaman publik Desain Web sebelum login:

1. **Landing Page — `http://localhost:5173/`**
   - Uji tab tahapan alur kerja (`01 Import`, `02 Draft`, `03 Export`).
   - Scroll ke simulasi **Optical Privacy Lens**, klik tombol **`Shielded`** vs **`Unfiltered`**:
     - `Shielded`: data sensitif IP/hostname/payload disamarkan (`Metadata only`).
     - `Unfiltered`: menampilkan tampilan mentah sebagai perbandingan.
2. **Alur Kerja — `http://localhost:5173/about`**
   - Klik bergantian ke-4 langkah proses (`Stage 01/04` s.d. `04/04`) dan pastikan penjelasan tiap stage berubah dengan jelas.
3. **Demo Interaktif — `http://localhost:5173/solutions`**
   - Ketik kata kunci di kotak pencarian, coba filter severity (`Critical`, `High`, dll.), dan uji toggle **`Exclude from report`** pada daftar temuan (`VF-001` s.d. `VF-008`).
4. **Detail Temuan & Dekripsi Demo — `http://localhost:5173/solutions/VF-001`**
   - Ubah metrik pada kalkulator **CVSS v3.1** (skor numerik dan badge severity berubah real-time).
   - Pada bagian bukti teknis terenkripsi, masukkan passphrase demo:
     ```text
     VULNFLOW-DEMO-2026
     ```
     Pastikan bukti PoC terdekripsi dengan benar.
5. **Pricing, Estimator & Enterprise Inquiry — `http://localhost:5173/contact`**
   - Geser slider jumlah aset:
     - **<= 10 Assets** (mis. `5 Assets`) → pastikan paket menampilkan **Free** (`Rp 0 / month`, `3 PDF exports/month`).
     - **11–50 Assets** → **Pro** (`Rp 750.000 / month`, `30 PDF exports/month`).
     - **> 50 Assets** → **Enterprise**.
   - Isi form **Enterprise inquiry** (`Full name`, `Company or team`, `Work email`, `Team size`, `Volume, private LLM / on-premise & target notes`, selesaikan verifikasi anti-bot CAPTCHA — tantangan aritmetika Math-HMAC bawaan atau widget Cloudflare Turnstile jika `TURNSTILE_SITE_KEY` & `TURNSTILE_SECRET_KEY` diisi — dan centang persetujuan **NDA**) lalu klik **`Submit Enterprise inquiry`**.
   - Pastikan konfirmasi inquiry muncul dan cek **Mailpit (`http://localhost:8025`)** bahwa email notifikasi lead Enterprise terkirim ke `sales@vulnflow.local` (dan entri tersimpan di database untuk ditinjau Superadmin di Skenario 6).
6. **Public Report Provenance Verification — `http://localhost:5173/verify`**
   - Masukkan kode acak (mis. `VF-0000-0000-0000`) lalu klik **`Verify ID`** → pastikan status menampilkan **`NOT FOUND`**.
   - *(Uji kode valid `VF-XXXX-XXXX-XXXX` setelah mengekspor PDF pada Skenario 3F di bawah.)*

---

## Skenario 2 — Role `MANAGER` (Setup Workspace, Proyek & Undangan Tim)

### A. Registrasi Workspace Baru (`/app/register`)
1. Buka `http://localhost:5173/app/register`.
2. Isi form:
   - **Full name:** `Budi Manager`
   - **Work email:** `manager.demo@vulnflow.local`
   - **Workspace name:** `Garuda Cyber Security`
   - **Password:** `Str0ng!Passw0rd2026` (min. 8 karakter, ada huruf besar, kecil, angka, dan simbol)
3. Klik submit. Pastikan langsung masuk ke `/app/dashboard` dengan sidebar menampilkan `Garuda Cyber Security (Manager)` dan badge `Free`.
   - *(Catatan kebijakan kuota: setiap akun dibatasi maksimal **1 workspace `FREE` pribadi** (`MAX_FREE_WORKSPACES_PER_USER = 1`). Pembuatan workspace `FREE` kedua lewat Workspace Switcher akan ditolak dengan pesan batas kuota, sedangkan workspace tambahan tetap dapat diikuti via undangan tim atau upgrade paket.)*

### B. Membuat Proyek & Rules of Engagement (`/app/projects`)
1. Klik menu **`Projects`** → klik **`New project`**.
2. Isi detail proyek:
   - **Project name:** `Core Banking Q4 Assessment`
   - **Client name:** `Bank Nusantara`
   - **Timezone:** `Asia/Jakarta` (atau sesuai pilihan)
   - **Start date & time:** pilih waktu sebelum saat ini (agar proyek langsung aktif menerima import)
   - **End date & time:** pilih tanggal beberapa hari/minggu ke depan
   - **(Opsional) Target Tech Stack:** pilih `Primary language` (mis. `Python`), `Framework` (mis. `FastAPI`), dan `Database` (mis. `PostgreSQL`) agar narasi & saran kode perbaikan AI lebih relevan tanpa mengirim data target/PoC sensitif.
   - **Authorized target scope (one domain, IP, or CIDR per line):** *(1 entri per baris, bukan dipisah koma)*
     ```text
     *.bank-target.local
     10.10.20.0/24
     ```
3. Simpan proyek. Pastikan kartu proyek berstatus `IN ROE` (aktif) muncul dan otomatis terpilih pada dropdown `Project` di topbar.

### C. Mengundang `PENTESTER` dan `VIEWER` (`/app/settings`)
1. Klik menu **`Settings`** → tab **`Team & Workspaces`**.
2. Pada form undangan anggota:
   - Masukkan `pentester.demo@vulnflow.local`, pilih role **`Pentester`**, lalu klik **`Send invite`**.
   - Masukkan `viewer.demo@vulnflow.local`, pilih role **`Viewer`**, lalu klik **`Send invite`**.
3. Buka **Mailpit (`http://localhost:8025`)** di tab browser baru:
   - Pastikan dua email undangan berbahasa Inggris terkirim untuk kedua alamat email di atas.
   - Anda bisa menyalin URL registrasi dari isi email di Mailpit, atau dari banner hijau di halaman Settings (`Copy link`).

### D. Uji Reset Password Organik (Opsional)
1. Di jendela Incognito, buka `http://localhost:5173/app/forgot-password` → masukkan email salah satu akun yang sudah terdaftar → submit.
2. Cek **Mailpit (`http://localhost:8025`)** → buka email *Password Reset* → klik link `/app/reset-password?token=...` dan uji ganti password.

---

## Skenario 3 — Role `PENTESTER` (Ingest Temuan, Triage, AI Draft & Export PDF)

### A. Menerima Undangan sebagai `PENTESTER`
1. Buka **Incognito Window** baru, tempel link undangan `pentester.demo@vulnflow.local` (`/app/register?invite=...`).
2. Perhatikan halaman menampilkan `Accept workspace invitation` dan kolom `Workspace name` otomatis hilang.
3. Isi **Full name** (`Siti Pentester`), email sudah terisi / sesuaikan `pentester.demo@vulnflow.local`, **Password** (`Str0ng!Passw0rd2026`), lalu submit.
4. Pastikan di pojok kiri bawah sidebar tertulis role **`Pentester`** pada workspace `Garuda Cyber Security`.

### B. Verifikasi Batasan RBAC `PENTESTER`
- **`/app/projects`:** `Pentester` dapat membuat/mengedit proyek (`New project` & `Edit`), tetapi dropdown **`Project Lead`** tidak muncul (khusus `Manager`).
- **`/app/settings`:**
  - Tab **`Activity Log`** menampilkan: *"Only Workspace Managers can view the activity log."*
  - Pada tab **`Team & Workspaces`**, form `Invite member`, ubah role, hapus anggota, rename, dan `Delete Workspace` tidak tampil.
  - Tab **`CLI API Keys`** dapat diakses penuh.

### C. Menambah Temuan Manual + Scope Quarantine (`/app/triage`)
1. Buka **`Findings`** (`/app/triage`), klik **`Add Finding`**, lalu buat **Temuan 1 (In-Scope)**:
   - **Finding title:** `SQL Injection in Login Endpoint`
   - **Category (CWE):** pilih `CWE-89`
   - **Protocol:** `https`
   - **Target host:** `auth.bank-target.local` *(cocok dengan `*.bank-target.local`)*
   - **Port:** `443`
   - **Endpoint path:** `/api/v1/auth/login`
   - Atur metrik pada **CVSS v3.1 Score Builder** (mis. Network / Low / None / Unchanged / High / High / High → `9.8 Critical`).
   - Isi **Raw evidence (HTTP / PoC)** dengan payload HTTP request/response dan langkah reproduksi → simpan.
2. Klik **`Add Finding`** lagi, buat **Temuan 2 (Out-of-Scope)**:
   - **Finding title:** `Exposed Admin Panel on Unlisted Host`
   - **Category (CWE):** pilih salah satu CWE (mis. `CWE-200` / `CWE-287`)
   - **Target host:** `rogue.outside-scope.test` *(tidak ada di scope proyek)*
   - Simpan → perhatikan filter `Out of Scope` bertambah 1 dan temuan ini otomatis dikarantina (`Out of Scope`) serta checkbox **`Include in report`** nonaktif agar tidak bocor ke laporan klien.

### D. Uji Push via CLI Lokal (Organik End-to-End)
1. Buka tab **`CLI API Keys`** di `/app/settings` (atau klik **`Import CLI`** di topbar kanan atas).
2. Buat API key (mis. label `Laptop Pentester`) → salin token yang hanya muncul 1 kali tersebut.
3. Siapkan contoh hasil scan Nuclei (`.jsonl`) atau gunakan CLI `vulnflow` di terminal:
   ```powershell
   uv run vulnflow configure --token <API_KEY> --workspace <WORKSPACE_ID> --api-url http://localhost:5173
   uv run vulnflow status
   uv run vulnflow push --project <PROJECT_ID> --file <path_ke_scan.jsonl> --type nuclei
   ```
4. Refresh `/app/triage` → pastikan temuan dari Nuclei langsung masuk (beserta deteksi duplikasi saat `push` diulang).

### E. Triage, Dekripsi PoC & Upload Screenshot (`/app/triage`)
1. Klik baris `SQL Injection in Login Endpoint` untuk membuka **Finding Detail Drawer**.
2. Pastikan bagian **`Protected Technical Evidence`** langsung mendekripsi raw proof (`Encrypted at rest (Key v1) · Access logged`).
3. Pada area drag-and-drop **`Evidence Screenshots`**, unggah 1 gambar `.png` atau `.jpg` (< 5 MB) → pastikan thumbnail tampil normal (disajikan dari MinIO).
4. Ubah status temuan (mis. `OPEN` → `IN_REVIEW`). Coba ubah satu temuan percobaan ke `FALSE_POSITIVE` → pastikan checkbox laporan otomatis tidak tercentang dan terkunci (EC-12).

### F. Menyusun Narasi AI & Ekspor PDF Free Tier (`/app/ai-review` & `/app/theme`)
1. Buka **`Report Draft`** (`/app/ai-review`).
2. Pastikan badge `Privacy protected` tampil (IP/host/PoC tidak ikut dikirim ke Gemini, atau Ollama lokal bila `LLM_PROVIDER=ollama`).
3. Pilih bahasa (`English (Executive)` atau `Bahasa Indonesia`) dan tone (`Executive Formal`), lalu klik **`Generate Draft`**.
   - Perhatikan progress antrean async Celery (`Queueing AI draft job...` s.d. `100%`) — jika temuan/stack identik pernah digenerate sebelumnya, hasil tersaji cepat dari prompt cache Redis.
4. Setelah narasi selesai dibuat (`AI Ghostwriter`):
   - Uji toggle **`Edit`** dan **`Preview`**.
   - Edit sedikit teks lalu klik **`Save Draft`** dan **`Approve Draft`** (status berubah `APPROVED`).
5. Buka **`Branding & PDF`** (`/app/theme`):
   - Perhatikan notice: *"View-only: only Workspace Managers can change branding settings."* (warna/logo terkunci bagi Pentester).
   - Pastikan opsi laporan profesional aktif: **`Include AI executive summary & guidance`** (`APPROVED`), **`Include cover page`**, **`Include Table of Contents & Document Control`**, **`Include Scope, Methodology & SLA Matrix`** (field **`Methodology`** default `OWASP WSTG & PTES`), dan **`Include CVSS risk radar chart`**.
   - Klik **`Export PDF Report`** → tunggu progress bar mencapai `100%` → pada kartu **`Exported Reports`**, perhatikan tag `Free watermark · Pixel-locked` dan tautan **`Verify (VF-XXXX-XXXX-XXXX)`**.
   - Klik **`Download PDF`**: buka PDF yang terunduh dan pastikan tiap halaman sudah di-*rasterize* (teks/watermark `FREE TIER PREVIEW` menyatu sebagai gambar sehingga tidak dapat dihapus lewat editor PDF biasa) serta memuat kode/QR verifikasi.
   - Klik tautan **`Verify (VF-...)`** untuk membuka `/verify/VF-...`: pastikan status **`VALID RECORD`** muncul, lalu unggah file PDF hasil unduhan ke bagian **Verify Local PDF File (Zero Upload)** untuk memastikan SHA-256 checksum lokal cocok 100%.

---

## Skenario 4 — Kembali ke `MANAGER` (Approval Scope, Branding, Billing & Audit)

Kembali ke jendela browser utama milik `manager.demo@vulnflow.local`:

1. **Assign Lead & Approval Karantina:**
   - Di `/app/projects`, pilih `Siti Pentester (Pentester)` pada dropdown **`Project Lead`**.
   - Di `/app/triage`, filter `Out of Scope only`, buka drawer `Exposed Admin Panel on Unlisted Host` → perhatikan tombol **`Approve into scope`** hanya muncul bagi `Manager`. (Uji klik jika memang ingin memasukkannya ke scope).
2. **Branding Workspace (`/app/theme`):**
   - Pilih salah satu preset warna (**`Deep Navy`**, **`Obsidian Slate`**, **`Forest Emerald`**, **`Crimson`**) atau ubah hex warna + lihat indikator WCAG **`Cover contrast`** (`>= 4.5:1`).
   - Ubah teks **`Confidentiality notice`**, klik **`Save branding`**, lalu lihat perubahan warna pada **Live Cover Preview** di sebelah kanan.
   - *(Catatan: tombol **`Upload logo`** akan aktif menggantikan `Unlock custom logo with Pro →` setelah workspace naik ke tier `PRO`.)*
3. **Billing & Kuota (`/app/billing`):**
   - Periksa bar **`Monthly PDF exports`** (mis. `1 / 3 reports (2 remaining)`).
   - Klik **`Upgrade to Pro`**:
     - Checkout Midtrans Snap Sandbox akan terbuat dengan format `order_id` `ORD-<hex>-<ts>` (`47` karakter) serta membuka modal **`Midtrans Checkout`** (*Open payment page*).
     - Setelah menyelesaikan simulasi pembayaran di halaman Midtrans Sandbox (atau via simulasi webhook SHA-512 lokal untuk demo cepat), klik **`Sync payment status`** untuk memverifikasi workspace naik ke paket `PRO` (`30` kuota bulanan, bebas watermark & *rasterize*, serta upload logo custom PNG di `/app/theme` terbuka).
4. **Audit Log Workspace (`/app/settings` → Tab `Activity Log`):**
   - Pastikan seluruh aktivitas penting sebelumnya (`POC_DECRYPTED`, `REPORT_COMPILED`, `AI_NARRATIVE_GENERATED`, `PROJECT_UPDATED`, dll.) tercatat lengkap dengan timestamp & IP.

---

## Skenario 5 — Role `VIEWER` (Akses Read-Only Klien & Proteksi Zero-PoC)

1. Buka **Incognito Window** baru, daftar lewat link undangan `viewer.demo@vulnflow.local` dari **Mailpit (`http://localhost:8025`)**.
2. Pastikan di pojok kiri bawah sidebar tertulis role **`Viewer`**.
3. Uji pembatasan di setiap halaman:
   - **`/app/dashboard` & `/app/projects`:** Dapat melihat ringkasan & daftar proyek, tetapi tidak ada tombol `New project` maupun `Edit`, dan `Project Lead` hanya berupa teks statis.
   - **`/app/triage`:**
     - Tidak ada tombol `Add Finding`, tidak bisa mencentang `Include in report`, dan dropdown status terkunci (`disabled`).
     - Klik salah satu temuan untuk membuka drawer → pada **`Protected Technical Evidence`**, pastikan bukti PoC mentah **tidak ditampilkan / diblokir** dengan pesan: *"Technical proof decryption is restricted to Workspace Managers and Pentesters."*
   - **`/app/ai-review`:** Hanya membaca narasi final; tombol `Generate Draft`, `Save Draft`, dan `Approve Draft` tidak tersedia.
   - **`/app/theme`:** Branding dan tombol `Export PDF Report` disembunyikan, namun pada **`Exported Reports`**, Viewer **tetap bisa mengklik `Download PDF`** untuk mengunduh laporan hasil audit.
   - **`/app/billing`:** Tombol upgrade bertuliskan `Only Managers can upgrade` (`disabled`).
   - **`/app/settings`:**
     - Tab `CLI API Keys`: *"View-only members cannot create or revoke CLI API keys."*
     - Tab `Activity Log`: *"Only Workspace Managers can view the activity log."*
     - Tab `Account Security`: tetap bisa mengatur TOTP 2FA pribadi.

---

## Skenario 6 — Role `SUPERADMIN` (`admin@vulnflow.local`)

### A. Login dengan Challenge MFA (TOTP)
1. Pastikan Anda sudah `Sign out` atau buka jendela Incognito baru menuju `http://localhost:5173/app/login`.
2. Masukkan:
   - **Work email:** `admin@vulnflow.local`
   - **Password:** sesuai nilai `SEED_ADMIN_PASSWORD` di `.env` (default `.env.example`: `VulnFlow-Seed-Admin-2026!`)
3. Klik **`Sign in`**. Sistem akan menolak login awal (`401`) dan memunculkan kotak **`Two-factor authentication required`** (*6-digit verification code*).
4. Generate kode TOTP 6 digit dari terminal:
   ```powershell
   uv run python scripts/dev.py totp
   ```
5. Ketik 6 digit tersebut (perhatikan sisa detik berlakunya) → klik **`Verify & Sign in`**.

### B. Verifikasi Portal Superadmin Terisolasi (`/app/admin`)
1. Setelah login, perhatikan URL otomatis mengarah ke **`/app/admin`** (bukan `/app/dashboard`).
2. Periksa sidebar & topbar:
   - Bagian atas sidebar menampilkan **`Platform Scope`** + badge **`Superadmin`** (bukan Workspace Switcher atau badge `Free`/`Pro`).
   - Menu sidebar **hanya** berisi **Platform** (`AI Usage`, `Users`, `Audit Logs`) dan **Account** (`Account Security`), serta pada halaman `/app/admin` tersedia 4 tab (**`AI Usage`**, **`Users`**, **`Workspaces & Plans`**, dan **`Audit Logs`**).
   - Tidak ada menu `Overview`, `Projects`, `Findings`, `Report Draft`, `Branding & PDF`, `Billing`, dropdown `Project`, maupun tombol **`Import CLI`**.
   - Footer kiri bawah menampilkan `VulnFlow Admin` · `Platform Superadmin`.
3. Uji isolasi route: ketik manual `http://localhost:5173/app/projects` atau `http://localhost:5173/app/billing` di browser → pastikan otomatis di-redirect kembali ke `/app/admin`.
4. Klik **`Website`** di pojok kanan atas untuk ke `/` → perhatikan tombol CTA di navbar berubah menjadi **`Admin Console`**.

### C. Menguji Fitur Governance Superadmin
1. **Tab `AI Usage` (`/app/admin`):**
   - Periksa metrik **`Total AI Tokens`**, **`Monthly Estimated Cost`** (USD & IDR), **`Template Fallback Rate`**, **`Monthly Spend Limit`**, serta tabel penggunaan per workspace (workspace `Garuda Cyber Security` dari Skenario 3 muncul di sini).
   - Ubah angka **`Monthly AI Spend vs Limit (USD)`** (mis. `150`) → klik **`Save spend limit`** dan pastikan tersimpan.
2. **Tab `Users` (`/app/admin?tab=users`):**
   - Cari `viewer.demo@vulnflow.local` di kotak pencarian.
   - Klik **`Suspend`**, masukkan alasan (mis. `Pengujian suspend akun`), lalu konfirmasi → status berubah `SUSPENDED`.
   - Coba login menggunakan `viewer.demo@vulnflow.local` di Incognito lain → pastikan ditolak (`403`).
   - Kembali ke tab `Users`, klik **`Activate`** untuk memulihkan akses akun tersebut.
3. **Tab `Workspaces & Plans` (`/app/admin?tab=workspaces`):**
   - Periksa antrean **`Enterprise Inquiries`** (inquiry yang dikirim dari `/contact` pada Skenario 1 tampil di sini).
   - Uji tombol **`Provision Enterprise`** atau modal edit subscription pada salah satu workspace untuk mengubah tier (`FREE`/`PRO`/`ENTERPRISE`), `Monthly PDF quota`, dan `Custom CLI batch limit` (mis. `2000`), beserta audit reason wajib.
4. **Tab `Audit Logs` (`/app/admin?tab=audits`):**
   - Filter berdasarkan action (mis. `USER_SUSPENDED`, `AI_NARRATIVE_GENERATED`, atau `SUBSCRIPTION_ADMIN_OVERRIDE`), lalu klik teks JSON pada kolom **`Details`** untuk membuka modal **`Activity Details`**.
5. **Menu `Account Security` (`/app/settings`):**
   - Pastikan hanya muncul kartu **`Two-Factor Authentication (TOTP)`** dengan status `Enabled`, tanpa tab workspace maupun kartu hapus akun.

---

## Pembersihan Setelah Selesai Testing (Opsional)

- Hentikan Vite dev server dengan menekan `Ctrl + C` di terminal frontend.
- Hentikan stack Docker bila sudah selesai (data DB/MinIO tetap tersimpan di Docker volume):
  ```powershell
  docker compose down
  ```
- Jika ingin mereset total database & object storage ke kondisi bersih awal:
  ```powershell
  docker compose down -v
  ```
