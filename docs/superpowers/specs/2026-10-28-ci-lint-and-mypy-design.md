# CI Enhancement (Linting & Formatting) and Mypy Type Checking — Design Spec (fastiq)

Date: 2026-10-28
Status: Draft, awaiting approval (no implementation yet)

## 1. Background

FastIQ has a comprehensive test suite (60 tests) and an automated GitHub Actions CI workflow running on Python 3.12 and 3.14 with `uv`.

However:
- **No linter or code formatter** is enforced in the repository or in CI. Formatting discrepancies, unused imports, and lint warnings can be merged without detection.
- **No static type checking (Mypy)** is run in CI. FastIQ is built with modern FastAPI, Pydantic v2, and SQLAlchemy 2.0 (asyncio), which are designed around static types. While the codebase is heavily type-hinted, regressions in type contracts (e.g. schema mismatches, incorrect async return types) can slip in unnoticed.
- The CI workflow currently sets `cancel-in-progress: true` unconditionally. Pushes to `main` should run to completion so post-merge health is always verified.

A reference CI workflow provided from an external project demonstrates:
1. Concurrency configured to cancel obsolete runs only for pull requests:
   `cancel-in-progress: ${{ github.event_name == 'pull_request' }}`.
2. A fast, dedicated `lint` job running on `ubuntu-latest`:
   `ruff check .`, `ruff format --check .`, and `mypy`.
3. An aggregate status check (`ci-ok`) that requires the `lint` job to pass alongside the test matrix.

## 2. Goals

- Add Ruff for high-performance linting and formatting (`ruff check` and `ruff format`).
- Add Mypy with Pydantic v2 plugin for static type checking across `app/` and `tests/`.
- Enhance the GitHub Actions CI workflow with:
  - PR-only run cancellation (`cancel-in-progress: ${{ github.event_name == 'pull_request' }}`).
  - A dedicated `lint` job running Ruff and Mypy on `ubuntu-latest`.
  - Integration of `lint` into the `ci-ok` required check.
- Document local developer commands in `README.md` and `CLAUDE.md`.

## 3. Non-goals and Anti-goals

Non-goals:
- Re-architecting existing schemas or routers; FastIQ's modular architecture is already clean.
- Enforcing docstring style rules (e.g. pydocstyle `D` rules).

Anti-goals:
- Allowing type errors or lint failures to pass unnoticed by skipping `lint` in `ci-ok`.
- Introducing heavy runtime dependencies (Ruff and Mypy belong strictly in `[dependency-groups] dev`).
- Enabling formatting checks in CI before formatting the existing codebase.

## 4. Linting & Formatting Specification (Ruff)

### 4.1 Tool Selection
[Ruff](https://docs.astral.sh/ruff/) will be added to `[dependency-groups] dev` in `pyproject.toml`.

### 4.2 Configuration
In `pyproject.toml`:

```toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "F",    # Pyflakes
    "I",    # isort (import sorting)
    "B",    # flake8-bugbear
    "UP",   # pyupgrade
]
ignore = [
    "E501", # line too long (handled by formatter)
]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

### 4.3 Baseline Formatting Step
All existing files in `app/`, `tests/`, and scripts will be formatted with `uv run ruff format .` and autofixed with `uv run ruff check --fix .`.

## 5. Type Checking Specification (Mypy)

### 5.1 Architecture & Strategy
FastIQ is fully async and leverages Pydantic v2 and SQLAlchemy 2.0.
1. **Pydantic Plugin:** Mypy will use `pydantic.mypy` plugin to validate BaseModel initialization, field types, and config validation.
2. **Strictness Strategy:** Because FastIQ was developed with clean type hints, strict checking (`disallow_untyped_defs = true`, `check_untyped_defs = true`) can be enabled on `app/` immediately.
3. **Third-Party Overrides:** Packages lacking inline type annotations (e.g. `passlib`, `uuid6`, `asyncpg`) use targeted overrides.

### 5.2 Dependencies
Added to `[dependency-groups] dev` in `pyproject.toml`:
- `ruff>=0.4.0`
- `mypy>=1.10.0`

### 5.3 Mypy Configuration
In `pyproject.toml`:

```toml
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

## 6. CI Workflow Updates (`.github/workflows/ci.yml`)

### 6.1 Concurrency Adjustment
Update concurrency in `.github/workflows/ci.yml`:

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}
```

### 6.2 New `lint` Job
Add a dedicated `lint` job:

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

      - name: Mypy Type Check
        run: uv run mypy
```

### 6.3 Update `ci-ok`
Add `lint` to `needs`:

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

## 7. Developer Workflow

Developers can run checks locally:
```bash
# Lint code
uv run ruff check .

# Fix auto-fixable lint issues
uv run ruff check --fix .

# Check code formatting
uv run ruff format --check .

# Auto-format code
uv run ruff format .

# Run static type checking
uv run mypy
```

## 8. Acceptance Criteria

1. `uv run ruff check .` passes locally with 0 errors.
2. `uv run ruff format --check .` passes locally with 0 formatting modifications needed.
3. `uv run mypy` passes locally with 0 type errors.
4. `.github/workflows/ci.yml` contains `lint` job and updated concurrency setting.
5. In GitHub Actions CI, `lint` job runs and passes.
6. `ci-ok` gates merge on `lint` succeeding.
