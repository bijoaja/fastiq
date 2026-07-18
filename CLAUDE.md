# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Environment & Run
- Setup dependencies: `uv sync`
- Start local development server (with hot reload): `uv run uvicorn app.main:app --reload --port 8000`
- Run shell commands in virtual environment: `uv run <command>`

### Database & Migrations
- Generate migration: `uv run alembic revision --autogenerate -m "<description>"`
- Run migrations: `uv run alembic upgrade head`
- Rollback last migration: `uv run alembic downgrade -1`
- Seed database: `uv run python app/scripts/seed.py`

### Testing
- Run all tests: `uv run pytest`
- Run with verbose output: `uv run pytest -v`
- Run specific test file: `uv run pytest tests/test_smoke.py`

### Docker
- Run development stack (Postgres + API dev with hot-reload & volume mount):
  `docker compose -f docker-compose.dev.yml up --build`
- Run production stack (Postgres + API production build & healthcheck):
  `docker compose -f docker-compose.yml up --build`

---

## Architecture

The core rule: **models are centralized, business logic is modularized.**

Strict separation of concerns: **router → service → repository**. Routers never touch the database or contain business rules.

---

## Conventions to Enforce

- **Response envelope** — every endpoint returns this shape:
  - Success: `{"success": true, "message": "Success", "data": {...}}` (via `ApiResponse`)
  - List: same plus `"pagination": {...}` (via `ApiListResponse` and `PaginationInfo`)
  - Error: `{"success": false, "message": "...", "errors": [{"field": "...", "message": "..."}]}` (via `ApiErrorResponse`)
- **Pagination** shape: `{"page", "per_page", "total", "total_pages"}`.
- **Exceptions are handled globally** (`core/exceptions.py`) — raise subclass of `AppException` (e.g., `NotFoundException`, `BadRequestException`) from services. Do not write per-endpoint try/except blocks.
- **Logging** is structured and logs request details, exception traceback, duration, status, and custom request ID injected by middleware. Console and File (`logs/app.log`) outputs are configured.
- **Dependency Injection** handles DB session (`get_db`) and service/repository creation in `core/dependencies.py`.
- **Authentication & Security** — Use JWT access tokens (short-lived) and database-stored hashed refresh tokens. Enforce authentication on routes using the `get_current_user` dependency: `current_user: User = Depends(get_current_user)`.
- **Unauthorized Errors** — Raise `UnauthorizedException` (e.g. from invalid tokens) to automatically return a standardized 401 error envelope.
- Adding a new business feature should only require adding a `modules/<name>/` folder (router/service/repository/schemas) — it should never require touching `core/`.
