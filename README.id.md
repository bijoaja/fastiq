# FastIQ — Opinionated FastAPI Project Template

[![CI](https://github.com/bijoaja/fastiq/actions/workflows/ci.yml/badge.svg)](https://github.com/bijoaja/fastiq/actions/workflows/ci.yml)

FastIQ adalah sebuah **template project FastAPI** (starter kit) yang dirancang untuk mempercepat pengembangan REST API siap produksi dengan arsitektur yang bersih, modular, dan terstruktur dengan baik. Template ini menyediakan struktur project opinionated, pola standar, dan tooling modern.

**Fitur:** Arsitektur bersih dengan pemisahan tanggung jawab (Router → Service → Repository), layout berbasis modul, model terpusat, SQLAlchemy async dengan migrasi Alembic, autentikasi JWT, logging terstruktur dengan request ID, format response API standar, global exception handling, dukungan Docker (dev & prod), setup testing komprehensif, dan pemindaian keamanan.

**Bukan:** Dashboard admin, ORM generator, autentikasi pihak ketiga, background worker, sistem event-driven, atau microservices framework. Tambahkan sendiri sesuai kebutuhan.

---

## Mulai Cepat

**Prasyarat:** Python 3.12+, [uv](https://docs.astral.sh/uv/), PostgreSQL 17 (opsional jika pakai Docker), Docker & Compose (opsional).

**Install & Jalankan:**
```bash
git clone https://github.com/bijoaja/fastiq.git
cd fastiq
uv sync
cp .env.example .env
uv run uvicorn app.main:app --reload --port 8000
```

Atau dengan Docker:
```bash
docker compose -f docker-compose.dev.yml up --build
```

API tersedia di http://localhost:8000; dokumentasi interaktif di http://localhost:8000/docs.

---

## Dokumentasi

| Dokumen | Bahasa Inggris | Bahasa Indonesia |
|---------|---|---|
| **Memulai** (install, jalankan, setup env) | [GETTING_STARTED.md](docs/en/GETTING_STARTED.md) | [GETTING_STARTED.md](docs/id/GETTING_STARTED.md) |
| **Arsitektur** (struktur, best practices) | [ARCHITECTURE.md](docs/en/ARCHITECTURE.md) | [ARCHITECTURE.md](docs/id/ARCHITECTURE.md) |
| **Pengujian & CI** (pytest, ruff, mypy, bandit) | [TESTING.md](docs/en/TESTING.md) | [TESTING.md](docs/id/TESTING.md) |
| **Autentikasi** (JWT, protected routes) | [AUTHENTICATION.md](docs/en/AUTHENTICATION.md) | [AUTHENTICATION.md](docs/id/AUTHENTICATION.md) |
| **FAQ** | [FAQ.md](docs/en/FAQ.md) | [FAQ.md](docs/id/FAQ.md) |
| **Product Requirements** (desain & fitur) | [PRD.md](docs/en/PRD.md) | [PRD.md](docs/id/PRD.md) |
| **Berkontribusi** (workflow, style, test) | [CONTRIBUTING.md](docs/en/CONTRIBUTING.md) | [CONTRIBUTING.md](docs/id/CONTRIBUTING.md) |

---

## Perintah Cepat

```bash
# Development
uv run uvicorn app.main:app --reload --port 8000

# Database
uv run alembic revision --autogenerate -m "deskripsi"
uv run alembic upgrade head
uv run python app/scripts/seed.py

# Pemeriksaan kualitas
uv run pytest
uv run ruff check .
uv run ruff format .
uv run mypy
uv run bandit -q -r app -c pyproject.toml

# Docker
docker compose -f docker-compose.dev.yml up --build    # dev dengan hot reload
docker compose -f docker-compose.yml up --build         # production
```

---

## Layout Proyek

```
app/
├── config/          # Pengaturan, database, logging, keamanan
├── core/            # Exception, response, dependency, middleware
├── models/          # Model SQLAlchemy terpusat
├── modules/         # Fitur bisnis (users, auth, ...)
├── scripts/         # Seeder dan utilitas
├── utils/           # Helper
└── main.py          # Entrypoint aplikasi FastAPI

tests/               # Pytest suite
docs/                # Dokumentasi bilingual
alembic/             # Migrasi database
```

Setiap module berisi: `router.py` (HTTP), `service.py` (logika bisnis), `repository.py` (database), `schemas.py` (model Pydantic).

---

## Berkontribusi

Kontribusi diterima. Mulai dengan membaca [CONTRIBUTING.md](docs/id/CONTRIBUTING.md) (atau [Inggris](docs/en/CONTRIBUTING.md)).

Alur kerja utama:
1. Branch dari `main` (mis. `fix/auth-token`, `feat/users`)
2. Buat perubahan kecil dan terfokus
3. Jalankan test suite dan linter secara lokal
4. Commit dengan Conventional Commits (fix: ..., feat: ..., docs: ...)
5. Buka PR ke `main`

---

## Lisensi

MIT. Lihat [LICENSE](LICENSE).

---

**Bahasa:** [English](README.md) | Bahasa Indonesia
