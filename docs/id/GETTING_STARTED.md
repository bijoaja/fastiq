# Memulai dengan FastIQ

> **Bahasa:** Indonesia | [English](../en/GETTING_STARTED.md)

Panduan instalasi, menjalankan aplikasi, dan konfigurasi environment.

---

## 1. Kebutuhan Sistem (Requirements)

Untuk menjalankan proyek ini secara lokal, pastikan Anda memiliki perkakas berikut terinstal pada sistem Anda:
* **Python 3.12** atau versi terbaru
* **uv** (paket manager yang direkomendasikan). Jika belum terinstal, jalankan perintah:
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
* **Docker & Docker Compose** (jika ingin menjalankan menggunakan kontainer)
* **PostgreSQL 17** (jika dijalankan secara lokal tanpa Docker)

---

## 2. Instalasi & Setup Lokal

Ikuti langkah-langkah berikut untuk memulai pengembangan secara lokal:

1. **Clone repositori proyek ini:**
   ```bash
   git clone <repository_url> fastiq
   cd fastiq
   ```

2. **Salin file environment configuration:**
   ```bash
   cp .env.example .env
   ```

3. **Install dependensi & buat Virtual Environment menggunakan `uv`:**
   ```bash
   uv sync
   ```
   Perintah di atas akan secara otomatis mendeteksi Python yang sesuai, membuat folder `.venv`, dan menginstal seluruh dependensi yang tertera di `pyproject.toml` dan `uv.lock`.

4. **Konfigurasi Database Lokal:**
   Pastikan PostgreSQL server Anda menyala dan buatlah sebuah database bernama `fastiq`. Sesuaikan variabel `DATABASE_URL` di dalam file `.env` jika diperlukan. Nilai bawaan:
   ```env
   DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/fastiq
   ```

5. **Jalankan Migrasi Database:**
   Terapkan struktur tabel ke database lokal menggunakan Alembic:
   ```bash
   uv run alembic upgrade head
   ```

6. **Jalankan Seeder (Opsional):**
   Isi database dengan data awal / dummy (misalnya user awal):
   ```bash
   uv run python app/scripts/seed.py
   ```

---

## 3. Menjalankan Aplikasi

### Menjalankan Aplikasi secara Lokal
Jalankan development server menggunakan Uvicorn dengan flag `--reload`:
```bash
uv run uvicorn app.main:app --reload --port 8000
```
Aplikasi Anda akan berjalan di http://localhost:8000. Dokumentasi API interaktif dapat diakses di:
* **Swagger UI (OpenAPI):** http://localhost:8000/docs
* **ReDoc:** http://localhost:8000/redoc

### Menjalankan Aplikasi menggunakan Docker

FastIQ menyediakan konfigurasi Docker yang siap pakai untuk development dan production:

#### A. Mode Development (Hot Reload & Live Volumemount)
Menjalankan API beserta PostgreSQL menggunakan konfigurasi hot reload (perubahan kode lokal langsung direfleksikan di dalam kontainer):
```bash
docker compose -f docker-compose.dev.yml up --build
```
* API akan berjalan pada port `8000`.
* Database Postgres akan berjalan pada port `5432` dengan volume lokal agar data persisten.

#### B. Mode Production
Menjalankan API dalam mode production (menggunakan build multi-stage yang optimal, menjalankan aplikasi di bawah non-root user, dan menyertakan health check otomatis):
```bash
docker compose -f docker-compose.yml up --build
```

---

## 4. Environment Variables

Berikut adalah konfigurasi environment variables yang didukung oleh FastIQ (didefinisikan dalam `.env` atau dibaca dari environment OS):

| Nama Variabel | Deskripsi | Default |
|---|---|---|
| `APP_NAME` | Nama aplikasi FastAPI yang akan muncul di Swagger docs. | `FastIQ` |
| `APP_ENV` | Mode environment aplikasi (`local`, `development`, `production`). | `local` |
| `DEBUG` | Mengaktifkan mode debug (menampilkan error detail di response API). | `true` |
| `PORT` | Port tempat aplikasi FastAPI berjalan. | `8000` |
| `DATABASE_URL` | String koneksi database SQLAlchemy (wajib asinkron). | `postgresql+asyncpg://...` |
| `SECRET_KEY` | Kunci rahasia yang digunakan untuk JWT dan operasi kriptografi. | `super-secret-key-change-me` |
| `JWT_ALGORITHM` | Algoritma yang digunakan untuk enkripsi JWT. | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Waktu kedaluwarsa Access Token dalam menit. | `15` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Waktu kedaluwarsa Refresh Token dalam hari. | `7` |
