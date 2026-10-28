# Panduan Kontributor

> **Bahasa:** Indonesia | [English](../en/CONTRIBUTING.md)
> **Terakhir diverifikasi terhadap kode:** 2026-10-28

Terima kasih sudah mau berkontribusi ke FastIQ. Panduan ini hanya memuat hal yang benar-benar berlaku di repo ini. Jika ada yang tidak cocok dengan kenyataan, itu bug dokumentasi: silakan buka issue.

---

## 1. Menyiapkan Lingkungan

Prasyarat: [uv](https://docs.astral.sh/uv/) dan Git. Python tidak wajib terpasang; uv bisa mengunduhnya (project butuh Python 3.12 ke atas).

```bash
git clone https://github.com/bijoaja/fastiq.git
cd fastiq
uv sync
cp .env.example .env
uv run uvicorn app.main:app --reload --port 8000
```

Pastikan PostgreSQL berjalan dan database `fastiq` sudah dibuat. Sesuaikan `DATABASE_URL` di `.env` jika diperlukan.

---

## 2. Struktur Kode

```text
app/
├── config/          # Pengaturan, koneksi DB, logging
├── core/            # Komponen inti (dependency, exception, middleware, response)
├── models/          # Model SQLAlchemy terpusat
├── modules/         # Modul bisnis (satu subfolder per fitur: router, service, repository, schemas)
├── scripts/         # Script pembantu (seeder)
├── templates/       # Template Jinja
├── utils/           # Helper umum
└── main.py          # Entrypoint aplikasi
tests/               # Test suite pytest (fixtures di conftest.py)
docs/                # Dokumentasi bilingual (en/ dan id/)
```

Prinsip: **router → service → repository**. Router tidak boleh menyentuh database atau logika bisnis. Service menyimpan logika, Repository menangani database. Model dipusat di `app/models/` agar Alembic mudah melacak relasi.

Menambah fitur bisnis baru: buat folder `app/modules/<nama_fitur>/` dengan `router.py`, `service.py`, `repository.py`, `schemas.py`. Model baru di `app/models/<nama>.py`. Daftarkan router di `app/main.py`. Jangan ubah `app/core/`.

---

## 3. Menjalankan Test dan Linter

Test menggunakan pytest. Environment variables (seperti CI):

```bash
DATABASE_URL="sqlite+aiosqlite:///:memory:" SECRET_KEY="ci-secret-key-for-testing-only-do-not-use-in-production" uv run pytest
```

Menjalankan test tertentu:

```bash
uv run pytest tests/test_auth.py
uv run pytest tests/ -v
```

Linting & formatting menggunakan Ruff:

```bash
uv run ruff check .          # periksa lint
uv run ruff check --fix .    # perbaiki lint otomatis
uv run ruff format --check . # periksa formatting
uv run ruff format .         # format kode otomatis
```

Type checking menggunakan Mypy:

```bash
uv run mypy                  # periksa static type annotations
```

Keamanan kode dengan Bandit:

```bash
uv run bandit -q -r app -c pyproject.toml
```

Setiap `# nosec` wajib disertai alasan tertulis di baris yang sama.

CI berjalan di GitHub Actions pada setiap PR dan push ke `main`. Setiap perubahan logika non-trivial sebaiknya menambah test case di `tests/`.

---

## 4. Alur Kerja

1. Cari atau buka issue yang menjelaskan masalahnya.
2. Buat branch dari `main`, mis. `fix/auth-token`, `feat/user-validation`, `docs/update`.
3. Buat perubahan kecil dan terfokus. Satu PR satu tujuan.
4. Jalankan test suite: `DATABASE_URL="sqlite+aiosqlite:///:memory:" SECRET_KEY="..." uv run pytest`.
5. Commit dengan pesan Conventional Commits, mis. `fix: ...`, `feat: ...`, `docs: ...`.
6. Buka PR ke `main`. Cantumkan `Closes #<nomor>` di deskripsi supaya issue tertutup otomatis saat PR di-merge.
7. Di deskripsi PR, tulis apa yang diubah, bagaimana diverifikasi, dan apa yang **belum** diverifikasi.

---

## 5. Aturan Commit dan PR

* Author commit adalah Anda sendiri. Jangan menambahkan baris `Co-Authored-By` untuk alat atau orang yang tidak ikut menulis commit.
* Jangan commit folder hasil build. Commit `uv.lock` bila dependensi project berubah.
* Merge dilakukan oleh maintainer lewat GitHub.

---

## 6. Menulis Dokumentasi

* Dokumentasi ada dalam dua bahasa: `docs/id/` dan `docs/en/`, dengan nama file yang sama. Ubah keduanya dalam PR yang sama.
* `README.md` (Inggris) dan `README.id.md` (Indonesia) ada di root.
* Tulis hanya yang sudah dicek ke kode atau ke keluaran command. Fitur yang belum ada ditandai jelas sebagai rencana, bukan ditulis seolah sudah ada.
* Perintah, nama file, dan nama field (`app`, `models`, `router.py`, `uv run`) tidak diterjemahkan.

---

## 7. Melaporkan Masalah

Buka issue di <https://github.com/bijoaja/fastiq/issues>. Sertakan:

* versi Python, OS, dan cara install (clone atau via `pyartisan new`),
* langkah mengulang masalah dan keluaran lengkap,
* hasil yang diharapkan.
