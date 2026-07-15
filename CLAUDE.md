# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository status

**No code has been written yet.** This repository currently contains only `PRD.md` (the full product spec) and an empty `README.md`. There is no `pyproject.toml`, `requirements.txt`, `app/` directory, tests, or Docker setup yet — none of the build/lint/test commands below exist until they are scaffolded.

When asked to start implementing FastIQ, treat `PRD.md` as the single source of truth for structure and conventions — do not invent alternative layouts. Follow the MVP Roadmap in PRD.md §21 (Phase 1 → Foundation, Phase 2 → DX, Phase 3 → Production Ready) for build order rather than implementing everything at once.

## What FastIQ is

FastIQ is an opinionated **project template/starter kit** for FastAPI (not a framework), modeled after an existing Flask template called FlaskIQ. Its stated non-goals matter as much as its goals — it deliberately excludes: admin dashboard, code/ORM generators, OAuth providers, Celery/background workers, event-driven architecture, and microservice tooling. Don't add these unless explicitly asked.

## Planned tech stack (per PRD.md §5)

- FastAPI + Uvicorn
- SQLAlchemy 2.x + Alembic (migrations)
- Pydantic + Pydantic Settings (config)
- JWT for auth, passwords hashed, UUIDv7 for IDs
- Pytest for testing
- Poetry or `uv` for dependency management (undecided — check for a lockfile/`pyproject.toml` before assuming which one is in use)

## Architecture (per PRD.md §6-§9)

The core rule: **models are centralized, business logic is modularized.**

```
app/
├── main.py
├── config/         # settings.py, database.py, logger.py, security.py, constants.py
├── core/           # exceptions.py, responses.py, pagination.py, dependencies.py, enums.py, middleware.py
├── models/         # ALL SQLAlchemy ORM models live here (not inside modules) — keeps Alembic autodetect and cross-model relations simple
├── modules/        # one folder per business feature: users/, products/, orders/...
│   └── <feature>/
│       ├── router.py       # HTTP layer only — request in, validate, call service, return response. No business logic here.
│       ├── service.py      # business logic (create/update/login/register/etc.)
│       ├── repository.py   # all DB access (find_by_id, create, update, delete...)
│       └── schemas.py      # Pydantic request/response schemas for this module
├── scripts/        # seed.py, seeders/, commands.py
├── templates/      # Jinja templates, e.g. for emails (kept even though this is API-first)
└── tests/          # unit/, integration/, conftest.py
```

Strict separation of concerns: **router → service → repository**. Routers never touch the database or contain business rules; that's what makes new modules pluggable without touching core architecture (see PRD.md "Success Criteria").

## Conventions to enforce in generated code

- **Response envelope** — every endpoint returns this shape (PRD.md §10):
  - Success: `{"success": true, "message": "Success", "data": {...}}`
  - List: same plus `"pagination": {...}`
  - Error: `{"success": false, "message": "...", "errors": [{"field": "...", "message": "..."}]}`
- **Pagination** shape: `{"page", "per_page", "total", "total_pages"}` (PRD.md §11).
- **Exceptions are handled globally** (core/exceptions.py) — don't write per-endpoint try/except for validation, DB, not-found, auth, or 500 errors; add cases to the global handler instead.
- **Logging** is structured, includes request ID, method, path, duration, status; supports console + file output (PRD.md §13).
- **Security dependencies** (current user, role, optional permission checks) belong in `core/dependencies.py` / `config/security.py`, not scattered per-module.
- Adding a new business feature should only require adding a `modules/<name>/` folder (router/service/repository/schemas) — it should never require touching `core/`.

## Docker (planned, PRD.md §19)

Two compose files with distinct intents: `docker-compose.dev.yml` (hot reload, volume mounts, Postgres + optional Redis) and `docker-compose.yml` for production (multi-stage build, non-root user, healthcheck).
