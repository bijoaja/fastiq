# Pengujian, Kualitas Kode, dan CI

> **Bahasa:** Indonesia | [English](../en/TESTING.md)

---

## 1. Pengujian (Testing)

FastIQ menggunakan **Pytest** dengan database SQLite in-memory (`aiosqlite`) untuk menjalankan pengujian tanpa mengganggu database utama Anda.

* **Menjalankan seluruh pengujian:**
  ```bash
  uv run pytest
  ```
* **Menjalankan dengan output verbose:**
  ```bash
  uv run pytest -v
  ```
* **Menjalankan file pengujian tertentu:**
  ```bash
  uv run pytest tests/test_smoke.py
  ```

Konfigurasi pengujian diatur pada `tests/conftest.py` yang menyediakan fixture untuk database in-memory asinkron dan client HTTP asinkron.

---

## 2. Linting & Formatting

FastIQ menggunakan **Ruff** untuk linting dan formatting kode:
* **Periksa linting:**
  ```bash
  uv run ruff check .
  ```
* **Perbaiki linting otomatis:**
  ```bash
  uv run ruff check --fix .
  ```
* **Periksa formatting:**
  ```bash
  uv run ruff format --check .
  ```
* **Format kode otomatis:**
  ```bash
  uv run ruff format .
  ```

---

## 3. Type Checking

FastIQ menggunakan **Mypy** (dengan plugin Pydantic) untuk static type checking pada folder `app/`:
```bash
uv run mypy
```

---

## 4. Security Scan

FastIQ menggunakan **Bandit** (SAST) untuk memindai kode `app/`:
```bash
uv run bandit -q -r app -c pyproject.toml
```
Setiap `# nosec` wajib disertai alasan tertulis di baris yang sama.

### Pemindaian CVE dependensi (SCA)

Bandit hanya memindai kode Anda sendiri. Untuk memeriksa CVE pada dependensi, gunakan **pip-audit** terhadap lockfile:
```bash
uv export --frozen --no-emit-project --no-hashes -o requirements-audit.txt
uvx pip-audit -r requirements-audit.txt --no-deps --disable-pip
```
Di CI ini berjalan sebagai job `audit` terpisah. Job ini **tidak memblokir** (`continue-on-error`) dan tidak menjadi syarat `ci-ok`, sehingga CVE baru tidak menggagalkan PR yang tidak terkait. Periksa hasil job secara berkala dan naikkan versi dependensi yang terdampak (commit `uv.lock`). **Dependabot** (`.github/dependabot.yml`) juga membuka PR pembaruan mingguan untuk dependensi `uv` dan GitHub Actions.

---

## 5. Continuous Integration (CI)

FastIQ dilengkapi dengan workflow GitHub Actions (`.github/workflows/ci.yml`) yang berjalan otomatis pada setiap *pull request* dan *push* ke branch `main`. Workflow ini mencakup:
* Pemeriksaan linting & formatting dengan **Ruff** (`ruff check` dan `ruff format --check`)
* Static type checking dengan **Mypy** (`mypy`)
* Pemindaian keamanan kode dengan **Bandit**
* Pemindaian CVE dependensi dengan **pip-audit** (job `audit`, tidak memblokir)
* Verifikasi konsistensi lockfile (`uv lock --check`)
* Matrix pengujian di OS Ubuntu dengan **Python 3.12** dan **Python 3.14**
* Isolasi environment mandiri tanpa dependensi pada file `.env` lokal
