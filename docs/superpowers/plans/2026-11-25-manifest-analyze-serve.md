# fastiq analyze Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Manifest fastiq mendeklarasikan `scripts.analyze` supaya `pyartisan analyze` jalan, dan `serve --uv` dibuktikan jalan.

**Architecture:** Hanya edit `.pyartisan/manifest.yaml`. Engine ada di repo pyartisan (plan `2026-11-25-doctor-serve-analyze.md`, harus selesai dulu).

**Tech Stack:** YAML manifest, uv, ruff, bandit, mypy.

**Spec:** `docs/superpowers/specs/2026-11-25-manifest-check-serve-design.md` (akan di-rename ke `...-analyze-serve-design.md`).

## Global Constraints
- Perintah dari job `lint` di `.github/workflows/ci.yml`, semua lewat `uv run`: `ruff check .`, `ruff format --check .`, `bandit -q -r app -c pyproject.toml`, `mypy`.
- `scripts.serve` tetap `uv run uvicorn app.main:app --reload` (sudah diawali `uv run`, jadi `serve_uv` tidak perlu).
- Generator `make module/model` tidak boleh berubah.
- Tanpa baris atribusi di commit (author bijoaja).

## Review Focus
- Manifest tetap valid dan lolos `load_manifest`.
- `pyartisan make module demo` tetap menyisipkan marker di `app/main.py` (regresi).
- `analyze` jalan tanpa venv project: `uv run` memakai environment dari lockfile.
- `serve --docker` memakai `docker-compose.yml` (target `prod`), bukan mode dev: perilaku ini dicatat, bukan diubah.

---

### Task 1: Manifest `scripts.analyze`

**Files:**
- Modify: `.pyartisan/manifest.yaml` (blok `scripts`)

**Interfaces:**
- Consumes: skema `scripts.analyze` dari plan pyartisan Task 5: list `{name, cmd, fix?}`.

- [x] **Step 1: Edit blok `scripts`** menjadi:
```yaml
scripts:
  serve: "uv run uvicorn app.main:app --reload"
  analyze:
    - {name: ruff-check, cmd: "uv run ruff check .", fix: "uv run ruff check --fix ."}
    - {name: ruff-format, cmd: "uv run ruff format --check .", fix: "uv run ruff format ."}
    - {name: bandit, cmd: "uv run bandit -q -r app -c pyproject.toml"}
    - {name: mypy, cmd: "uv run mypy"}
```
  Catatan: key `fix` ditambah di plan ini (tidak ada di spec template). Update spec agar sinkron.
- [x] **Step 2: Validasi YAML:** `python -c "import yaml;print(len(yaml.safe_load(open('.pyartisan/manifest.yaml'))['scripts']['analyze']))"` -> `4`.
- [x] **Step 3: Uji:** `uv sync` lalu `pyartisan analyze` -> semua `✔`, exit 0. `pyartisan analyze --fix` -> tidak mengubah file bersih.
- [x] **Step 4: Uji serve:** `pyartisan serve --uv` -> uvicorn naik di port 8000.
- [x] **Step 5: Regresi:** `pyartisan make module demo` di salinan sementara -> berhasil.
- [x] **Step 6: Commit** `git add .pyartisan/manifest.yaml docs/superpowers && git commit -m "feat(manifest): add analyze steps"`

### Task 2: Verifikasi bandit CI dan cakupan

**Files:**
- Modify: `.github/workflows/ci.yml` dan `.pyartisan/manifest.yaml` (hanya jika scope diperluas)

- [x] **Step 1:** `grep -n "bandit" .github/workflows/ci.yml` -> step `bandit -q -r app -c pyproject.toml` ada di job `lint`.
- [x] **Step 2:** Cek kode Python di luar `app/` (selain `tests`, `alembic`, yang dikecualikan `[tool.bandit]`): `git ls-files "*.py" | grep -v "^app/\|^tests/\|^alembic/"`. Ada kode produksi -> perluas `-r app <path>` di CI dan manifest bersamaan. Tidak ada -> tidak ada perubahan.
- [x] **Step 3:** Jika berubah: `git commit -m "ci: widen bandit scope"`. (Tidak ada perubahan, cakupan app/ sudah tepat).
