# Test Structure — Design Spec (fastiq)

Date: 2026-10-27
Status: Draft, awaiting approval (no implementation yet)

## 1. Background

fastiq already has the structure the other two repos are moving to. `tests/` holds 14 files named
`test_<module>.py` plus a `conftest.py`: 1,052 lines and 60 tests in total, run with pytest. They
pass on Python 3.12 and 3.14 on Windows (`uv sync --frozen`, then `uv run pytest`).

So this spec does **not** split anything. It writes down the conventions that already exist so the
other repos and future contributors follow the same ones, and records what was found while checking.

Current files (tests per file): `test_auth_repository` 4, `test_auth_router` 2, `test_auth_schemas` 5,
`test_auth_service` 8, `test_core` 3, `test_database` 3, `test_middleware` 3,
`test_refresh_token_model` 1, `test_security_tokens` 5, `test_seeder` 1, `test_smoke` 1,
`test_users_router` 7, `test_users_schemas` 8, `test_users_service` 10.

## 2. Goals

- A short, written convention for test layout, naming, fixtures and commands.
- The test settings the suite depends on are explicit, not accidental (see section 5).

## 3. Non-goals and anti-goals

Non-goals: moving or renaming existing test files, adding tests for untested areas, coverage
thresholds, lint, changing pytest-asyncio or other dependency versions.

Anti-goals: renaming files for style while changing no behavior; a reorganization that lowers the test count (60) or weakens an assertion.

## 4. Conventions (as they exist today)

- One file per module or layer: `test_<module>.py`, with the layer in the name when the module name
  repeats (`test_auth_router`, `test_auth_service`, `test_auth_repository`, `test_auth_schemas`).
- Shared fixtures live only in `tests/conftest.py`: an in-memory SQLite engine (`sqlite+aiosqlite:///:memory:`, `StaticPool`),
  a session-scoped `setup_db` (create and drop all tables), a `db` session that clears every table after each test,
  and an `httpx.AsyncClient` `client` fixture with `get_db` overridden.
- Async tests need the project's pytest-asyncio setup (`asyncio_mode = "strict"` in `pyproject.toml`), so each async test is marked explicitly.
- `pythonpath = "."` in `pyproject.toml` makes `import app` work from the repo root.
- Commands (from `CLAUDE.md`): `uv run pytest`, `uv run pytest -v`, `uv run pytest tests/test_smoke.py`.
- New tests go in the file of the module they test; a new module gets a new `test_<module>.py`.

## 5. Findings to record

1. **The tests need two settings that come from the environment.** `app.config.settings` requires
   `DATABASE_URL` and `SECRET_KEY`. Run in a clean copy with no `.env`, the suite fails during
   collection with `Field required` for both. Run with `DATABASE_URL=sqlite+aiosqlite:///:memory:`
   and `SECRET_KEY` set in the environment and no `.env`, all 60 tests pass (Python 3.12, Windows).
   So CI must set these variables itself.
2. **`.env` is tracked in git.** `git ls-files` lists `.env` (added in `6c24469`) although `.gitignore`
   contains `.env`. A check showed its keys and values are identical to `.env.example` and the secret
   is a placeholder starting `super-se...` (68 characters), so it does not look like a real secret.
   It is still a risk pattern: someone may later put a real value in a tracked file.
   **Decision (user): untrack it in a separate small PR**, not as part of the test or CI work:
   `git rm --cached .env` (the file stays in `.gitignore`), plus a README note telling users to copy
   `.env.example` to `.env`. Side effect to accept: a project made with `pyartisan new fastapi` will
   no longer contain `.env`, so the app will not start until that copy is made. The CI workflow
   deletes the checked-out `.env` anyway, so it does not depend on whether this PR has merged.
3. `conftest.py` overrides the `event_loop` fixture at session scope. Newer pytest-asyncio releases
   deprecate that override. The lockfile pins a working version today; which version is locked was not checked.
4. One warning appears in every run: Starlette says using `httpx` with `starlette.testclient` is deprecated. It does not fail the run.

## 6. Acceptance

- This document is committed under `docs/superpowers/specs/` and matches `tests/` (14 files, 60 tests).
- No file under `tests/` changes as part of this spec.
- If the owner wants finding 2 fixed, it is a separate issue and PR.

## 7. Left to the builder

Nothing to build. If the conventions are later copied into `CLAUDE.md` or a contributor guide, that is a documentation task.
