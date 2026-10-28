# FastIQ — Opinionated FastAPI Project Template

[![CI](https://github.com/bijoaja/fastiq/actions/workflows/ci.yml/badge.svg)](https://github.com/bijoaja/fastiq/actions/workflows/ci.yml)

FastIQ is a **FastAPI project template** (starter kit) designed to accelerate development of production-ready REST APIs with clean, modular, and well-structured architecture. It provides opinionated project structure, standardized patterns, and modern tooling.

**Features:** Clean architecture with separation of concerns (Router → Service → Repository), modular feature-based layout, centralized models, async SQLAlchemy with Alembic migrations, JWT authentication, structured logging with request ID tracking, standardized API response format, global exception handling, Docker support (dev & prod), comprehensive testing setup, and security scanning.

**Not:** Admin dashboards, ORM generators, third-party auth, background workers, event-driven systems, or microservices frameworks. Add these yourself as needed.

---

## Getting Started

**Requirements:** Python 3.12+, [uv](https://docs.astral.sh/uv/), PostgreSQL 17 (optional if using Docker), Docker & Compose (optional).

**Install & Run:**
```bash
git clone https://github.com/bijoaja/fastiq.git
cd fastiq
uv sync
cp .env.example .env
uv run uvicorn app.main:app --reload --port 8000
```

Or with Docker:
```bash
docker compose -f docker-compose.dev.yml up --build
```

API available at http://localhost:8000; interactive docs at http://localhost:8000/docs.

---

## Documentation

| Document | English | Indonesian |
|----------|---------|------------|
| **Getting Started** (install, run, env setup) | [GETTING_STARTED.md](docs/en/GETTING_STARTED.md) | [GETTING_STARTED.md](docs/id/GETTING_STARTED.md) |
| **Architecture** (structure, best practices) | [ARCHITECTURE.md](docs/en/ARCHITECTURE.md) | [ARCHITECTURE.md](docs/id/ARCHITECTURE.md) |
| **Testing & CI** (pytest, ruff, mypy, bandit) | [TESTING.md](docs/en/TESTING.md) | [TESTING.md](docs/id/TESTING.md) |
| **Authentication** (JWT, protected routes) | [AUTHENTICATION.md](docs/en/AUTHENTICATION.md) | [AUTHENTICATION.md](docs/id/AUTHENTICATION.md) |
| **FAQ** | [FAQ.md](docs/en/FAQ.md) | [FAQ.md](docs/id/FAQ.md) |
| **Product Requirements** (design & features) | [PRD.md](docs/en/PRD.md) | [PRD.md](docs/id/PRD.md) |
| **Contributing** (workflow, code style, tests) | [CONTRIBUTING.md](docs/en/CONTRIBUTING.md) | [CONTRIBUTING.md](docs/id/CONTRIBUTING.md) |

---

## Quick Commands

```bash
# Development
uv run uvicorn app.main:app --reload --port 8000

# Database
uv run alembic revision --autogenerate -m "description"
uv run alembic upgrade head
uv run python app/scripts/seed.py

# Quality checks
uv run pytest
uv run ruff check .
uv run ruff format .
uv run mypy
uv run bandit -q -r app -c pyproject.toml

# Docker
docker compose -f docker-compose.dev.yml up --build    # dev with hot reload
docker compose -f docker-compose.yml up --build         # production
```

---

## Project Layout

```
app/
├── config/          # Settings, database, logging, security
├── core/            # Exceptions, responses, dependencies, middleware
├── models/          # Centralized SQLAlchemy models
├── modules/         # Business features (users, auth, ...)
├── scripts/         # Seeders and utilities
├── utils/           # Helpers
└── main.py          # FastAPI app entrypoint

tests/               # Pytest suite
docs/                # Bilingual documentation
alembic/             # Database migrations
```

Every module contains: `router.py` (HTTP), `service.py` (business logic), `repository.py` (database), `schemas.py` (Pydantic models).

---

## Contributing

Contributions welcome. Start by reading [CONTRIBUTING.md](docs/en/CONTRIBUTING.md) (or [Indonesian](docs/id/CONTRIBUTING.md)).

Key workflow:
1. Branch from `main` (e.g., `fix/auth-token`, `feat/users`)
2. Keep changes small and focused
3. Run test suite and linters locally
4. Commit with Conventional Commits (fix: ..., feat: ..., docs: ...)
5. Open PR to `main`

---

## License

MIT. See [LICENSE](LICENSE).

---

**Language:** English | [Indonesian](README.id.md)
