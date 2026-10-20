# VulnFlow AI

SaaS platform manajemen kerentanan & asisten pelaporan untuk pentester  mengagregasi hasil pemindaian (Nmap/Nuclei) dari CLI lokal, melakukan triase & kalkulasi CVSS, lalu menyusun laporan PDF dengan bantuan AI yang dijamin tidak pernah menerima data sensitif target (IP, port, PoC mentah).

> Proyek mata kuliah **Implementasi Perancangan Perangkat Lunak (IPPL)**, dikembangkan dengan metodologi **Spec-Driven Development** + **Test-Driven Development**. Frontend web (`apps/web`) juga memenuhi rubrik mata kuliah **Desain Web** (lihat [Lintas Mata Kuliah](#lintas-mata-kuliah-desain-web) di bawah).

## Dokumentasi Lengkap

Spesifikasi mengikat ada di `../DOCS/` (di luar folder ini), **bukan** di README ini:

| Dokumen                                                                | Isi                                                                      |
|:---------------------------------------------------------------------- |:------------------------------------------------------------------------ |
| [`SRS.md`](../DOCS/SRS.md)                                             | Kebutuhan fungsional, use case, NFR (apa yang dibangun)                  |
| [`SDD.md`](../DOCS/SDD.md)                                             | Arsitektur C4, ERD, kontrak REST API, wireframe (bagaimana membangunnya) |
| [`EDGE_CASES_AND_RESILIENCE.md`](../DOCS/EDGE_CASES_AND_RESILIENCE.md) | 18 kasus batas (EC-01..EC-18) wajib teruji                               |
| [`PLAN.md`](../DOCS/PLAN.md)                                           | Checklist kerja per fase (FASE 0-7) & standar mutu kode                  |

README ini hanya memandu *cara menjalankan* proyek — untuk *keputusan desain/kebutuhan*, selalu rujuk dokumen di atas.

## Tech Stack

| Layer               | Teknologi                                                      |
|:------------------- |:-------------------------------------------------------------- |
| Backend API         | Python 3.12+, FastAPI, SQLAlchemy 2.0, Alembic, Celery + Redis |
| Database            | PostgreSQL 16                                                  |
| Object Storage      | MinIO (S3-compatible)                                          |
| CLI Agent           | Python 3.12+, Typer, Rich, HTTPX                               |
| Web Dashboard       | Vue 3 (Composition API), Vite, Tailwind CSS, shadcn-vue        |
| Shared Contracts    | Pydantic V2 (`packages/contracts`, dipakai bersama API & CLI)  |
| Package/Dep Manager | [`uv`](https://docs.astral.sh/uv/) (workspace monorepo)        |

## Struktur Monorepo

```
vulnflow-ai/
├─ apps/
│  ├─ api/            # FastAPI backend (app/models, app/domain, app/routers, app/workers)
│  ├─ cli/             # CLI agent (vulnflow/) — entrypoint: `vulnflow`
│  └─ web/             # Vue 3 SPA — rute publik (Desweb) + dashboard terautentikasi (IPPL)
├─ packages/
│  └─ contracts/       # Pydantic V2 schemas bersama (vulnflow_contracts/)
├─ scripts/
│  └─ check_quality.py # Gerbang mutu satu pintu (lint, type, security, test, audit)
├─ docker-compose.yml  # PostgreSQL, Redis, MinIO (lokal/dev)
├─ .env.example        # Salin ke .env, isi kredensial sendiri
└─ pyproject.toml      # uv workspace root + konfigurasi ruff/mypy/pytest/bandit
```

## Prasyarat

- [Python 3.12+](https://www.python.org/)
- [`uv`](https://docs.astral.sh/uv/getting-started/installation/) — **install lewat installer resmi**, bukan `pip install uv`, agar otomatis masuk PATH.
- [Docker](https://www.docker.com/) + Docker Compose — untuk PostgreSQL, Redis, MinIO lokal.
- Node.js 20+ — baru dibutuhkan mulai FASE 6 (`apps/web`).

## Setup Awal

```bash
# 1. Salin template environment variable, isi dengan kredensial sendiri
cp .env.example .env

# 2. Nyalakan infrastruktur lokal (Postgres, Redis, MinIO)
docker compose up -d

# 3. Install seluruh dependensi workspace (apps/api, apps/cli, packages/contracts)
uv sync --all-packages

# 4. Pastikan CLI terpasang dengan benar
uv run vulnflow --version
```

## Menjalankan Gerbang Mutu

Wajib dijalankan setelah setiap sub-tugas selesai (lihat `PLAN.md` §4):

```bash
uv run python scripts/check_quality.py
```

- **Mode default (FASE 0-6):** Ruff/Mypy/Bandit/pip-audit selalu *zero-tolerance*; coverage test dievaluasi proporsional terhadap kode yang sudah ada — direktori test yang belum dibuat tidak dianggap gagal.

- **Mode `--final` (FASE 7.3, gerbang akhir):** menegakkan ambang keras 85% coverage + seluruh 18 test resilience (EC-01..EC-18) harus ditemukan dan lolos.
  
  ```bash
  uv run python scripts/check_quality.py --final
  ```

## Status Proyek

Lihat tracker lengkap di [`PLAN.md`](../DOCS/PLAN.md). Ringkasan saat ini:

- [x] Dokumentasi (SRS, SDD, Edge Cases) — selesai
- [x] **FASE 0** — Monorepo scaffolding, `docker-compose`, linter/type-checker, `check_quality.py` — selesai & terverifikasi (`uv sync --all-packages` resolve bersih, gerbang mutu jalan end-to-end)
- [x] FASE 1 — Pydantic V2 Shared Contracts — Selesai 29 unit test, coverage 94%
- [ ] FASE 2-7 — lihat `PLAN.md`

## Lintas Mata Kuliah: Desain Web

`apps/web` sengaja disatukan untuk memenuhi dua mata kuliah sekaligus dalam satu basis kode:

- **Rute Publik** (`/`, `/about`, `/solutions`, `/solutions/:id`, `/contact`) — tanpa login, data mock, memenuhi rubrik wajib mata kuliah Desain Web. Spesifikasi UI/UX lengkapnya ada di `../Desweb/DOCS/Dokumentasi_Proyek_Desweb_VulnFlow_AI.docx` (rujukan mengikat, tidak diduplikasi di `SDD.md`).
- **Rute Terautentikasi** (`/app/*`) — dashboard SaaS VulnFlow AI yang sesungguhnya, untuk mata kuliah IPPL.

Detail lengkap: `SRS.md` Bab 4.10 (FR-PUB) dan `SDD.md` §4.2.
