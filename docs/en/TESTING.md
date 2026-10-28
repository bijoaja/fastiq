# Testing, Code Quality, and CI

> **Language:** English | [Indonesian](../id/TESTING.md)

---

## 1. Testing

FastIQ uses **Pytest** with in-memory SQLite database (`aiosqlite`) to run tests without affecting your main database.

* **Run all tests:**
  ```bash
  uv run pytest
  ```
* **Run with verbose output:**
  ```bash
  uv run pytest -v
  ```
* **Run a specific test file:**
  ```bash
  uv run pytest tests/test_smoke.py
  ```

Test configuration is defined in `tests/conftest.py`, which provides fixtures for async in-memory database and async HTTP client.

---

## 2. Linting & Formatting

FastIQ uses **Ruff** for code linting and formatting:
* **Check linting:**
  ```bash
  uv run ruff check .
  ```
* **Auto-fix linting issues:**
  ```bash
  uv run ruff check --fix .
  ```
* **Check formatting:**
  ```bash
  uv run ruff format --check .
  ```
* **Auto-format code:**
  ```bash
  uv run ruff format .
  ```

---

## 3. Type Checking

FastIQ uses **Mypy** (with Pydantic plugin) for static type checking on the `app/` folder:
```bash
uv run mypy
```

---

## 4. Security Scan

FastIQ uses **Bandit** (SAST) to scan the `app/` code:
```bash
uv run bandit -q -r app -c pyproject.toml
```
Every `# nosec` comment must include a written reason on the same line.

### Dependency CVE scan (SCA)

Bandit only scans your own code. To check dependencies for known CVEs, use **pip-audit** against the lockfile:
```bash
uv export --frozen --no-emit-project --no-hashes -o requirements-audit.txt
uvx pip-audit -r requirements-audit.txt --no-deps --disable-pip
```
In CI this runs as the separate `audit` job. It is **non-blocking** (`continue-on-error`) and `ci-ok` does not require it, so a newly published CVE does not fail unrelated PRs. Check the job result regularly and bump the affected dependency (commit `uv.lock`). **Dependabot** (`.github/dependabot.yml`) also opens weekly update PRs for `uv` dependencies and GitHub Actions.

---

## 5. Continuous Integration (CI)

FastIQ includes a GitHub Actions workflow (`.github/workflows/ci.yml`) that runs automatically on every pull request and push to `main`. The workflow includes:
* Code linting & formatting checks with **Ruff** (`ruff check` and `ruff format --check`)
* Static type checking with **Mypy** (`mypy`)
* Code security scanning with **Bandit**
* Dependency CVE scan with **pip-audit** (`audit` job, non-blocking)
* Lockfile consistency verification (`uv lock --check`)
* Test matrix on Ubuntu with **Python 3.12** and **Python 3.14**
* Isolated environment without relying on local `.env` file
