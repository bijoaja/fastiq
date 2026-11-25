# Desain fastiq: `scripts.analyze`, bandit CI

> Tanggal: 2026-11-25. Plan: `../plans/2026-11-25-manifest-analyze-serve.md`.
> Engine: spec di repo pyartisan `docs/superpowers/specs/2026-11-25-doctor-serve-analyze-design.md`.

## Tujuan
- `pyartisan analyze` di fastiq menjalankan perintah CI lint.
- `pyartisan serve --uv` jalan tanpa perubahan: `scripts.serve` sudah `uv run uvicorn ...`.
- Bandit tetap di CI dengan cakupan yang sama dengan `check`.

## Bukan tujuan
Tidak mengubah kode aplikasi, deps, atau Dependabot.

## Perubahan `.pyartisan/manifest.yaml`
```yaml
scripts:
  serve: "uv run uvicorn app.main:app --reload"
  analyze:
    - {name: ruff-check, cmd: "uv run ruff check .", fix: "uv run ruff check --fix ."}
    - {name: ruff-format, cmd: "uv run ruff format --check .", fix: "uv run ruff format ."}
    - {name: bandit, cmd: "uv run bandit -q -r app -c pyproject.toml"}
    - {name: mypy, cmd: "uv run mypy"}
```
`serve_uv` tidak perlu: `scripts.serve` sudah diawali `uv run`.

## Bandit (poin 4)
Sudah ada di `ci.yml` (`bandit -r app`) dan `[tool.bandit]` (`exclude_dirs = ["tests", "alembic"]`). Verifikasi saja. `app` cukup selama kode aplikasi hanya di `app/`. Cek apakah ada kode di luar `app/` (mis. skrip di root) yang perlu masuk scope. Keputusan di plan, tandai sebagai pilihan implementer.

## Pengujian
- `pyartisan analyze` di fastiq: semua lulus.
- `pyartisan serve --uv` dan `--docker` jalan (`docker-compose.yml` memakai target `prod`).
- `pyartisan make module x` tetap jalan (regresi manifest).

## Catatan
`uv run` di `analyze` memastikan alat dari lockfile project, bukan env pyartisan. Perlu pyartisan yang mengenal `scripts.analyze`.
