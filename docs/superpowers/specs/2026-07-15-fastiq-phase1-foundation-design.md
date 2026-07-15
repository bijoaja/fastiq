# FastIQ Phase 1 (Foundation) — Design Spec

**Date:** 2026-07-15
**Status:** Approved by user, pending self-review
**Scope:** MVP Roadmap Phase 1 only (PRD.md §21). Phase 2 (auth, pagination utilities, seeder framework, pytest suite, health check) and Phase 3 (CI/CD, roles, pre-commit) are explicitly out of scope for this iteration.

## Context

`PRD.md` is a complete product spec for FastIQ, an opinionated FastAPI project template (sibling to an existing FlaskIQ template). The repository currently has no code — only the PRD and an empty README. This spec turns Phase 1 of the PRD's roadmap into a concrete, buildable design: FastAPI setup, config layer, async database + SQLAlchemy 2.x, Alembic, Docker (dev & prod), basic logging, standardized response envelope, global exception handling, and one example module (`users`) demonstrating the router → service → repository pattern.

Decisions locked in during brainstorming:
- **Dependency manager:** `uv` (already installed; Poetry is not installed and PRD left this undecided).
- **Database mode:** SQLAlchemy 2.x **async** (asyncpg), even though the PRD only mentions "async repository template" under Future Enhancements — chosen because FastAPI is async-native and starting sync now means a breaking rewrite later.
- **`/health` endpoint:** included now (minimal, no DB check) purely so Docker's `HEALTHCHECK` has a real target — full health-check feature (DB ping, dependency checks) stays Phase 2 per roadmap.
- **Test scaffolding:** one smoke test (`tests/test_users.py` + `conftest.py`) included now as the project's required runnable self-check, even though the formal "Testing setup (Pytest)" roadmap item is Phase 2. This is not the full unit/integration/API test strategy from PRD §17 — that's deferred.
- **Directory layout:** follows PRD §6 tree literally — `tests/`, `scripts/`, `utils/`, `templates/` all live inside `app/`, not at repo root.

## Architecture

### Directory structure

```
fastiq/
├── pyproject.toml, uv.lock, .python-version
├── .env.example, .gitignore, .dockerignore
├── Dockerfile                  # multi-stage: base → dev / prod targets
├── docker-compose.dev.yml      # hot reload, volume mount, postgres:17
├── docker-compose.yml          # prod build, postgres:17, healthcheck
├── alembic/, alembic.ini
├── README.md
└── app/
    ├── __init__.py
    ├── main.py                 # app factory, lifespan, middleware, exception handlers, routers, /health
    ├── config/
    │   ├── settings.py         # Pydantic Settings, reads .env/.env.local/.env.production
    │   ├── database.py         # async engine, async_sessionmaker, DeclarativeBase, get_db dependency
    │   ├── logger.py           # dictConfig: console + RotatingFileHandler
    │   ├── security.py         # hash_password()/verify_password() only (JWT deferred to Phase 2)
    │   └── constants.py
    ├── core/
    │   ├── exceptions.py       # AppException hierarchy + register_exception_handlers(app)
    │   ├── responses.py        # ApiResponse / ApiListResponse envelope models + build helpers
    │   ├── pagination.py       # minimal offset-based paginate() helper (backs the list envelope)
    │   ├── dependencies.py     # re-exports get_db, shared pagination query-param dependency
    │   ├── enums.py
    │   └── middleware.py       # request-id (contextvar) + timing middleware, feeds log records
    ├── models/
    │   ├── __init__.py         # imports every model module so Base.metadata is complete for Alembic
    │   └── user.py             # demo User: id (uuid7 pk), email, hashed_password, name, timestamps
    ├── modules/
    │   └── users/
    │       ├── router.py       # POST /api/users, GET /api/users, GET /api/users/{id}
    │       ├── service.py      # create_user, list_users, get_user — business rules (e.g. dup email)
    │       ├── repository.py   # create, find_by_id, find_by_email, list_all
    │       └── schemas.py      # CreateUserRequest, UserResponse
    ├── scripts/
    │   ├── seed.py             # entrypoint: python -m app.scripts.seed
    │   └── seeders/user_seeder.py
    ├── templates/.gitkeep
    ├── tests/
    │   ├── conftest.py         # async httpx client fixture, aiosqlite in-memory test DB override
    │   └── test_users.py       # smoke test: create user → list → appears
    └── utils/uuid.py           # generate_uuid7() (via `uuid6` package; py3.12 stdlib has no uuid7)
```

### Request flow

`main.py` builds the FastAPI app, registers middleware (request-id → logging/timing), registers global exception handlers, includes the `users` router under `/api`, and exposes `GET /health` returning `{"status": "ok"}`. A request hits `router.py` (validates via `schemas.py`, no business logic) → calls `service.py` (business rules, raises `AppException` subclasses on failure) → calls `repository.py` (async SQLAlchemy queries via injected `AsyncSession`). Response is wrapped in the standard envelope before returning.

### Response & error envelope (PRD §10)

`core/responses.py` defines the shapes and helpers; every router return value goes through them, and the global handlers in `core/exceptions.py` produce the error shape automatically for `AppException`, `RequestValidationError`, and unhandled `Exception` (mapped to 500). No per-endpoint try/except.

### Database & migrations

`config/database.py` creates one async engine from `settings.DATABASE_URL` (asyncpg), an `async_sessionmaker`, and a `get_db` async-generator dependency that yields a session and guarantees close/rollback. `alembic/env.py` imports `app.models` (triggering `__init__.py`'s aggregation) and sets `target_metadata = Base.metadata` for autogenerate.

### Logging & middleware

`config/logger.py` configures a root logger via `dictConfig` — console handler always on, `RotatingFileHandler` writing to `logs/app.log` (dir created if missing). `core/middleware.py` generates a request ID per request (stored in a `contextvars.ContextVar`), times the request, and logs one line per request with method/path/status/duration/request_id. A logging `Filter` pulls the request ID from the contextvar so all log records within that request carry it.

### Docker

`Dockerfile` is multi-stage: `base` (installs `uv`, copies `pyproject.toml`/`uv.lock`, `uv sync`) → `dev` (adds reload, mounts source) and `prod` (copies app code, creates non-root user, `HEALTHCHECK CMD curl -f http://localhost:8000/health`). `docker-compose.dev.yml` runs the `dev` target with a bind-mounted volume and `postgres:17`. `docker-compose.yml` runs the `prod` target built from the image, plus `postgres:17`, no source bind mount.

## Testing

One smoke test proves the vertical slice works end-to-end: `tests/conftest.py` overrides `get_db` with an `aiosqlite` in-memory session and provides an `httpx.AsyncClient` fixture; `tests/test_users.py` posts a new user, then lists users and asserts it's present. Run via `uv run pytest`. This is intentionally minimal — full repository/service/API test suites are Phase 2 (PRD §17).

## Out of scope for this iteration (explicit deferrals)

- JWT login/register endpoints, current-user dependency, role/permission dependencies (Phase 2/3, PRD §14)
- Full pagination utilities beyond the minimal helper needed for the list envelope (Phase 2)
- Seeder **framework** beyond the one demo `user_seeder.py` + `seed.py` entrypoint (Phase 2 hardens this)
- CI/CD, pre-commit hooks (Phase 3)
- Full README/docs/architecture.md content beyond what Phase 1 features actually support (PRD §20) — README will document only what exists after this iteration
