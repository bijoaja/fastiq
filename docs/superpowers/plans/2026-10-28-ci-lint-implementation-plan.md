# FastIQ CI Linting & Formatting Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement Ruff linting and formatting in `fastiq`, format the existing codebase, and add a dedicated `lint` job with PR-specific concurrency to the GitHub Actions CI workflow.

**Architecture:**
1. Add `ruff>=0.4.0` to `[dependency-groups] dev` in `pyproject.toml`.
2. Configure Ruff in `pyproject.toml` (`line-length = 100`, `target-version = "py312"`, select `E, W, F, I, B, UP`).
3. Format and autofix existing codebase using Ruff before enabling CI checks.
4. Update `.github/workflows/ci.yml`:
   - Update `concurrency` to `cancel-in-progress: ${{ github.event_name == 'pull_request' }}`.
   - Add a separate `lint` job running `uv run ruff check .` and `uv run ruff format --check .`.
   - Update `ci-ok` to require `lint`.
5. Update `README.md` with developer commands.

**Tech Stack:** Python 3.12+, uv, Ruff, GitHub Actions.

---

### Task 1: Configure Ruff in `pyproject.toml`

**Files:**
- Modify: `pyproject.toml`
- Modify: `uv.lock`

- [ ] **Step 1: Add Ruff dependency and configuration**
  Update `pyproject.toml`:
  ```toml
  [dependency-groups]
  dev = [
      "pytest>=8.2.2",
      "pytest-asyncio>=0.23.7",
      "aiosqlite>=0.20.0",
      "httpx>=0.27.0",
      "ruff>=0.4.0",
  ]

  [tool.ruff]
  line-length = 100
  target-version = "py312"

  [tool.ruff.lint]
  select = ["E", "W", "F", "I", "B", "UP"]
  ignore = ["E501"]

  [tool.ruff.format]
  quote-style = "double"
  indent-style = "space"
  ```

- [ ] **Step 2: Update lockfile**
  Run `uv lock`.

---

### Task 2: Format and Clean Existing Codebase

**Files:**
- Modify: `app/**/*.py`, `tests/**/*.py`

- [ ] **Step 1: Run autofix and formatter**
  Run:
  ```bash
  uv run ruff check --fix .
  uv run ruff format .
  ```

- [ ] **Step 2: Verify zero lint and format errors**
  Run:
  ```bash
  uv run ruff check .
  uv run ruff format --check .
  ```
  Both commands must exit with code 0.

- [ ] **Step 3: Run existing tests to ensure no regressions**
  Run:
  ```bash
  DATABASE_URL="sqlite+aiosqlite:///:memory:" SECRET_KEY="ci-secret-key-for-testing-only" uv run --frozen pytest -q -p no:cacheprovider
  ```
  Ensure all 60 tests pass.

---

### Task 3: Update CI Workflow (`.github/workflows/ci.yml`)

**Files:**
- Modify: `.github/workflows/ci.yml`

- [ ] **Step 1: Update concurrency and add `lint` job**
  Update concurrency:
  ```yaml
  concurrency:
    group: ${{ github.workflow }}-${{ github.ref }}
    cancel-in-progress: ${{ github.event_name == 'pull_request' }}
  ```
  Add job `lint`:
  ```yaml
    lint:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
        - uses: astral-sh/setup-uv@v5
          with:
            enable-cache: true
            python-version: "3.12"
        - name: Sync dependencies
          run: uv sync --frozen --python 3.12
        - name: Ruff Check
          run: uv run ruff check .
        - name: Ruff Format Check
          run: uv run ruff format --check .
  ```
  Update `ci-ok` job:
  ```yaml
    ci-ok:
      runs-on: ubuntu-latest
      needs: [lint, test]
      if: always()
      steps:
        - name: Verify all jobs succeeded
          run: |
            if [ "${{ needs.lint.result }}" != "success" ] || [ "${{ needs.test.result }}" != "success" ]; then
              echo "CI checks failed: lint=${{ needs.lint.result }}, test=${{ needs.test.result }}"
              exit 1
            fi
            echo "all checks passed"
  ```

- [ ] **Step 2: Validate workflow syntax**
  Verify YAML with `python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"`.

---

### Task 4: Documentation & PR Submission

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update `README.md`**
  Add instructions for `uv run ruff check .` and `uv run ruff format .`.

- [ ] **Step 2: Commit, push, and open PR**
  - Branch: `feat/ci-lint`
  - Commit message: `feat: add Ruff linting and formatting to CI workflow`
  - Author only `bijoaja` (NO co-author).
  - Open PR to `main`.
