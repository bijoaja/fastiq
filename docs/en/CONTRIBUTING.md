# Contributor Guide

> **Language:** English | [Indonesian](../id/CONTRIBUTING.md)
> **Last verified against the code:** 2026-10-28

Thanks for wanting to contribute to FastIQ. This guide only lists things that actually hold in this repo. If something does not match reality, that is a documentation bug: please open an issue.

---

## 1. Setting up your environment

Prerequisites: [uv](https://docs.astral.sh/uv/) and Git. Python does not have to be installed; uv can download it (the project needs Python 3.12 or newer).

```bash
git clone https://github.com/bijoaja/fastiq.git
cd fastiq
uv sync
cp .env.example .env
uv run uvicorn app.main:app --reload --port 8000
```

Ensure PostgreSQL is running and the database `fastiq` is created. Adjust `DATABASE_URL` in `.env` if needed.

---

## 2. Code layout

```text
app/
├── config/          # Settings, database, logging
├── core/            # Core components (dependency, exception, middleware, response)
├── models/          # Centralized SQLAlchemy models
├── modules/         # Business modules (one subfolder per feature: router, service, repository, schemas)
├── scripts/         # Helper scripts (seeder)
├── templates/       # Jinja templates
├── utils/           # Common helpers
└── main.py          # Application entrypoint
tests/               # pytest test suite (fixtures in conftest.py)
docs/                # Bilingual documentation (en/ and id/)
```

Principle: **router → service → repository**. Routers must not touch the database or contain business logic. Services hold the logic, repositories handle the database. Models are centralized in `app/models/` so Alembic can easily track relationships.

To add a new business feature: create a folder `app/modules/<feature_name>/` with `router.py`, `service.py`, `repository.py`, `schemas.py`. New models in `app/models/<name>.py`. Register the router in `app/main.py`. Do not modify `app/core/`.

---

## 3. Running tests and linters

Tests use pytest. Environment variables (same as CI):

```bash
DATABASE_URL="sqlite+aiosqlite:///:memory:" SECRET_KEY="ci-secret-key-for-testing-only-do-not-use-in-production" uv run pytest
```

Run specific tests:

```bash
uv run pytest tests/test_auth.py
uv run pytest tests/ -v
```

Linting and formatting use Ruff:

```bash
uv run ruff check .          # check lint
uv run ruff check --fix .    # autofix lint issues
uv run ruff format --check . # check formatting
uv run ruff format .         # format code
```

Type checking uses Mypy:

```bash
uv run mypy                  # static type check
```

Security scanning uses Bandit:

```bash
uv run bandit -q -r app -c pyproject.toml
```

Every `# nosec` suppression must carry a written reason on the same line.

CI runs on GitHub Actions on every PR and push to `main`. Every non-trivial logic change should add test cases under `tests/`.

---

## 4. Workflow

1. Find or open an issue describing the problem.
2. Create a branch from `main`, e.g. `fix/auth-token`, `feat/user-validation`, `docs/update`.
3. Keep the change small and focused. One PR, one purpose.
4. Run the test suite: `DATABASE_URL="sqlite+aiosqlite:///:memory:" SECRET_KEY="..." uv run pytest`.
5. Commit with Conventional Commits style messages, e.g. `fix: ...`, `feat: ...`, `docs: ...`.
6. Open a PR to `main`. Put `Closes #<number>` in the description so the issue closes automatically when the PR is merged.
7. In the PR description, write what changed, how it was verified, and what was **not** verified.

---

## 5. Commit and PR rules

* The commit author is you. Do not add `Co-Authored-By` lines for tools or people who did not take part in writing the commit.
* Do not commit build output folders. Commit `uv.lock` when project dependencies change.
* Merging is done by the maintainer through GitHub.

---

## 6. Writing documentation

* Documentation exists in two languages: `docs/id/` and `docs/en/`, with the same file names. Change both in the same PR.
* `README.md` (English) and `README.id.md` (Indonesian) are in the root.
* Write only what has been checked against the code or against command output. Features that do not exist yet are clearly marked as plans, not written as if they exist.
* Commands, file names and field names (`app`, `models`, `router.py`, `uv run`) are not translated.

---

## 7. Reporting problems

Open an issue at <https://github.com/bijoaja/fastiq/issues>. Include:

* Python version, OS, and how you installed (clone or via `pyartisan new`),
* the steps to reproduce and the full output,
* the expected result.
