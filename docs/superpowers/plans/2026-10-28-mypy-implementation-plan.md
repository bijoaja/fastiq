# FastIQ Mypy Type Checking Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement static type checking using Mypy with Pydantic v2 plugin in `fastiq`, resolve any type errors in `app/`, and add Mypy verification to the CI workflow.

**Architecture:**
1. Add `mypy>=1.10.0` to `[dependency-groups] dev` in `pyproject.toml`.
2. Configure Mypy in `pyproject.toml` with `pydantic.mypy` plugin, `python_version = "3.12"`, `disallow_untyped_defs = true`, and overrides for third-party libraries (`passlib`, `uuid6`, `asyncpg`).
3. Run `uv run mypy app` locally and fix any identified type annotations or return types.
4. Add `uv run mypy app` to the CI `lint` job in `.github/workflows/ci.yml`.
5. Update `README.md` with developer commands.

**Tech Stack:** Python 3.12+, uv, Mypy, Pydantic v2, FastAPI, SQLAlchemy 2.0.

---

### Task 1: Add Mypy Dependency & Configure `pyproject.toml`

**Files:**
- Modify: `pyproject.toml`
- Modify: `uv.lock`

- [ ] **Step 1: Add Mypy to dev dependencies and configure tool**
  Update `pyproject.toml`:
  ```toml
  [dependency-groups]
  dev = [
      "pytest>=8.2.2",
      "pytest-asyncio>=0.23.7",
      "aiosqlite>=0.20.0",
      "httpx>=0.27.0",
      "ruff>=0.4.0",
      "mypy>=1.10.0",
  ]

  [tool.mypy]
  python_version = "3.12"
  files = ["app"]
  plugins = ["pydantic.mypy"]
  warn_unused_configs = true
  warn_redundant_casts = true
  warn_unused_ignores = true
  check_untyped_defs = true
  disallow_untyped_defs = true
  disallow_incomplete_defs = true

  [[tool.mypy.overrides]]
  module = [
      "passlib.*",
      "uuid6.*",
      "asyncpg.*",
  ]
  ignore_missing_imports = true

  [tool.pydantic-mypy]
  init_forbid_extra = true
  init_typed = true
  warn_required_dynamic_aliases = true
  ```

- [ ] **Step 2: Update lockfile**
  Run `uv lock`.

---

### Task 2: Run Mypy & Fix Type Annotations

**Files:**
- Modify: `app/**/*.py` (if any type adjustments needed)

- [ ] **Step 1: Run Mypy type check**
  Run:
  ```bash
  uv run mypy app
  ```

- [ ] **Step 2: Address any type errors**
  Ensure all return types and parameters in routers, services, repositories, and models pass strict validation without error.

- [ ] **Step 3: Verify existing tests**
  Run:
  ```bash
  DATABASE_URL="sqlite+aiosqlite:///:memory:" SECRET_KEY="ci-secret-key-for-testing-only" uv run --frozen pytest -q -p no:cacheprovider
  ```
  Ensure all 60 tests pass.

---

### Task 3: Integrate Mypy into CI Workflow

**Files:**
- Modify: `.github/workflows/ci.yml`

- [ ] **Step 1: Add Mypy step to `lint` job**
  In `.github/workflows/ci.yml`, append step to `lint` job:
  ```yaml
        - name: Mypy Type Check
          run: uv run mypy app
  ```

---

### Task 4: Documentation & PR Submission

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Document Mypy command in `README.md`**
  Add `uv run mypy app` to development and testing section.

- [ ] **Step 2: Commit, push, and open PR**
  - Branch: `feat/mypy-type-checking`
  - Commit message: `feat: add Mypy static type checking with Pydantic plugin`
  - Author only `bijoaja` (NO co-author).
  - Open PR to `main`.
