# FastIQ CI Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement automated continuous integration (CI) workflow using GitHub Actions for `fastiq` running on pull requests and pushes to `main`.

**Architecture:**
1. A GitHub Actions workflow `.github/workflows/ci.yml` runs on `pull_request` and `push` to `main`.
2. Environment isolation: job removes any checked-out `.env` file (`rm -f .env`) to guarantee tests only use explicitly supplied environment variables (`DATABASE_URL=sqlite+aiosqlite:///:memory:` and dummy `SECRET_KEY`).
3. Matrix execution: Ubuntu with Python 3.12 and Python 3.14 running `uv lock --check`, `uv sync --frozen`, and `uv run pytest -q`.
4. Aggregate status check job `ci-ok` that passes only when all matrix jobs succeed.

**Tech Stack:** GitHub Actions, uv, pytest, pytest-asyncio, FastAPI, SQLite (aiosqlite).

---

### Task 1: Create GitHub Actions Workflow File

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Write workflow configuration**
  Create `.github/workflows/ci.yml` with:
  - `name: ci`
  - Triggers: `pull_request`, `push: branches: [main]`, `workflow_dispatch`
  - `permissions: contents: read`
  - Concurrency group per ref with `cancel-in-progress: true`
  - Job `test`:
    - Matrix: `os: ubuntu-latest`, `python: ["3.12", "3.14"]`, `fail-fast: false`
    - Steps:
      - Checkout code via `actions/checkout@v4`
      - Remove checked out `.env`: `run: rm -f .env`
      - Setup uv via `astral-sh/setup-uv@v5` with `enable-cache: true`
      - Install Python: `run: uv python install ${{ matrix.python }}`
      - Verify lockfile: `run: uv lock --check`
      - Sync dependencies: `run: uv sync --frozen --python ${{ matrix.python }}`
      - Run tests: `run: uv run pytest -q -p no:cacheprovider`
        - Env:
          - `DATABASE_URL: "sqlite+aiosqlite:///:memory:"`
          - `SECRET_KEY: "ci-secret-key-for-testing-only-do-not-use-in-production"`
  - Job `ci-ok`:
    - `needs: [test]`
    - `runs-on: ubuntu-latest`
    - `if: always()`
    - Step verifying test job outcome (`exit 0` if `needs.test.result == 'success'`, else `exit 1`).

- [ ] **Step 2: Verify workflow locally**
  - Verify syntax with `python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"`.
  - Simulate the CI step commands locally:
    ```bash
    DATABASE_URL="sqlite+aiosqlite:///:memory:" SECRET_KEY="ci-secret-key-for-testing-only" uv run --frozen pytest -q -p no:cacheprovider
    ```
    Ensure all 60 tests pass.

- [ ] **Step 3: Commit and submit PR**
  - Commit message: `ci: add GitHub Actions workflow with uv and pytest matrix`
  - Open PR against `main`.

---

### Task 2: Update Documentation & GitHub Settings Guidelines

**Files:**
- Modify: `README.md` and/or `CLAUDE.md`

- [ ] **Step 1: Document CI in README**
  Add a badge or short section mentioning that CI tests against Python 3.12 and 3.14 using `uv` and `pytest`.

- [ ] **Step 2: Ruleset setup instructions**
  Provide guidelines for repo owner to enable GitHub branch protection / ruleset requiring `ci-ok` once the workflow is merged into `main`.
