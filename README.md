# FastIQ — Starter Kit & Project Template FastAPI yang Terstruktur dan Opiniated

FastIQ adalah sebuah template proyek (starter kit) berbasis **FastAPI** yang dirancang untuk mempercepat pembuatan REST API siap produksi dengan arsitektur yang bersih, modular, dan terstruktur dengan baik. FastIQ terinspirasi dari filosofi **FlaskIQ** dan dirancang khusus untuk memenuhi standar kebersihan kode dan pemisahan tanggung jawab (*Separation of Concerns*) yang ketat.

---

## 1. Filosofi & Prinsip Utama

FastIQ dibangun dengan memegang beberapa prinsip utama berikut:
1. **Opinionated (Beropini):** Struktur proyek sudah ditentukan secara jelas. Developer tidak perlu bingung memilih susunan direktori, penamaan file, maupun letak file konfigurasi.
2. **Modular:** Setiap fitur bisnis dikelompokkan ke dalam modulnya masing-masing (misalnya `users`, `products`, `orders`), sehingga mudah untuk diskalakan dan dirawat secara independen.
3. **Separation of Concerns (Pemisahan Tanggung Jawab):** Router hanya berfungsi sebagai lapisan HTTP (menerima input, memvalidasi skema, memanggil service, mengembalikan response). Logika bisnis diletakkan pada lapisan **Service**, sementara komunikasi dengan database ditangani oleh lapisan **Repository** (Router → Service → Repository).
4. **Production Ready (Siap Produksi):** Dilengkapi dengan logging terstruktur, error handling global, penanganan request ID, skema response terstandar, integrasi database asinkron, migrasi database via Alembic, pengujian via Pytest, dan konfigurasi Docker (development & production).

### Yang Bukan Menjadi Tujuan FastIQ (Non-Goals)
FastIQ dirancang agar tetap minimalis dan fokus. Oleh karena itu, FastIQ secara sengaja **tidak menyediakan**:
* Admin Dashboard
* ORM Generator & Code Generator otomatis
* Penyedia Autentikasi Pihak Ketiga (seperti OAuth Google, dll.)
* Background Worker (seperti Celery/Redis Queue)
* Event-Driven Architecture maupun framework Microservices

Semua fitur di atas dapat ditambahkan secara mandiri oleh developer sesuai kebutuhan proyek masing-masing.

---

## 2. Fitur FastIQ (Phase 1 & 2)

* **Arsitektur Modular & Pemisahan Concern:** Struktur bersih yang memisahkan Router, Service, dan Repository.
* **Model Database Terpusat:** Semua model SQLAlchemy diletakkan di direktori `app/models/` untuk memudahkan auto-deteksi oleh Alembic dan mempermudah relasi antar-model.
* **Manajemen Dependency modern dengan `uv`:** Menggunakan `uv` yang sangat cepat untuk isolasi virtual environment dan instalasi package yang efisien.
* **Skema Response Terstandar:** Menjamin setiap endpoint mengembalikan format JSON yang konsisten, baik untuk response sukses tunggal (`ApiResponse`), response list dengan paginasi (`ApiListResponse`), maupun response error (`ApiErrorResponse`).
* **Paginasi Terstandar:** Response list dilengkapi metadata paginasi yang konsisten (`page`, `per_page`, `total`, `total_pages`).
* **Exception Handling Global:** Menangani error validasi, HTTP exception, database error, unauthorized, forbidden, hingga internal server error di satu tempat (`app/core/exceptions.py`).
* **Logging Terstruktur:** Mencatat Request, Response, Exception, dan SQL query secara detail ke Console dan File (`logs/app.log`) dengan melampirkan Request ID unik per request.
* **Request ID Middleware:** Melampirkan header `X-Request-ID` secara otomatis pada request dan response untuk mempermudah tracking log.
* **Database Asinkron:** Konfigurasi koneksi database modern dan asinkron menggunakan SQLAlchemy 2.x dan driver `asyncpg`.
* **Migrasi Database:** Terintegrasi dengan Alembic untuk manajemen migrasi database yang mudah.
* **Database Seeder:** Framework seeder yang terstruktur di direktori `app/scripts/seed.py` untuk mengisi database dengan data awal.
* **Docker Ready:** Dilengkapi dengan target build Multi-Stage untuk development (hot-reload, volume mounts, Postgres) dan production (optimalisasi image, non-root user, healthcheck).
* **Testing Ready:** Konfigurasi pengujian asinkron menggunakan Pytest dan SQLite (`aiosqlite`) sebagai database test in-memory.

---

## 3. Kebutuhan Sistem (Requirements)

Untuk menjalankan proyek ini secara lokal, pastikan Anda memiliki perkakas berikut terinstal pada sistem Anda:
* **Python 3.12** atau versi terbaru
* **uv** (paket manager yang direkomendasikan). Jika belum terinstal, jalankan perintah:
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
* **Docker & Docker Compose** (jika ingin menjalankan menggunakan kontainer)
* **PostgreSQL 17** (jika dijalankan secara lokal tanpa Docker)

---

## 4. Instalasi & Setup Lokal

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

## 5. Menjalankan Aplikasi

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

## 6. Environment Variables

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

---

## 7. Struktur Proyek

Struktur proyek FastIQ dirancang agar modular dan mudah dipahami:

```text
fastiq/
├── alembic/                # Konfigurasi & file versi migrasi database
├── app/
│   ├── config/             # Pengaturan aplikasi, koneksi database, logging, & konstanta
│   │   ├── constants.py    # Konstanta aplikasi
│   │   ├── database.py     # Setup SQLAlchemy Async Engine & Session
│   │   ├── logger.py       # Konfigurasi log terstruktur (Console & File)
│   │   ├── security.py     # Enkripsi & utilitas keamanan (JWT, hashing)
│   │   └── settings.py     # Konfigurasi aplikasi berbasis Pydantic Settings
│   ├── core/               # Komponen inti aplikasi
│   │   ├── dependencies.py # Dependency Injection (repository, service)
│   │   ├── exceptions.py   # Global Exception Handler & Custom Exceptions
│   │   ├── middleware.py   # Middleware seperti RequestLogging (Request ID)
│   │   ├── pagination.py   # Helper untuk standarisasi paginasi
│   │   └── responses.py    # Skema standar Response API (ApiResponse, ApiErrorResponse)
│   ├── models/             # SEMUA model ORM SQLAlchemy (terpusat untuk memudahkan Alembic)
│   │   └── user.py         # Model user
│   ├── modules/            # Modul fitur bisnis (satu subfolder per modul)
│   │   ├── auth/           # Modul Autentikasi (JWT)
│   │   │   ├── repository.py # Operasi database untuk token refresh
│   │   │   ├── router.py   # API Endpoints (Register, Login, Refresh, Logout)
│   │   │   ├── schemas.py  # Skema request & response autentikasi
│   │   │   └── service.py  # Logika bisnis autentikasi & manajemen token
│   │   └── users/          # Modul Users
│   │       ├── repository.py # Operasi database khusus modul users
│   │       ├── router.py   # API Endpoints (Hanya HTTP Layer, bebas dari logic)
│   │       ├── schemas.py  # Skema validasi request & response (Pydantic)
│   │       └── service.py  # Logika bisnis utama modul users
│   ├── scripts/            # Script pembantu (seperti seeder)
│   │   ├── seed.py         # Runner untuk database seeding
│   │   └── seeders/        # Kumpulan seeder per-tabel/modul
│   ├── templates/          # Folder untuk template Jinja (misal template email)
│   ├── utils/              # Helper dan utilitas umum (seperti UUID generator)
│   └── main.py             # Entrypoint aplikasi FastAPI (pendaftaran router & middleware)
├── docs/                   # Dokumentasi tambahan proyek
├── tests/                  # File pengujian unit & integrasi menggunakan Pytest
├── Dockerfile              # Dockerfile Multi-stage (target: base, dev, prod)
├── docker-compose.dev.yml  # Compose development
├── docker-compose.yml      # Compose production
├── pyproject.toml          # Definisi dependensi & konfigurasi testing
└── uv.lock                 # Lockfile dependensi python
```

---

## 8. Database Migrasi (Alembic)

Setiap ada perubahan pada model SQLAlchemy di dalam folder `app/models/`, Anda harus membuat file versi migrasi baru.

* **Membuat File Migrasi Baru (Auto-generate):**
  Alembic akan secara otomatis membandingkan model Anda dengan kondisi database saat ini dan membuat file migrasi baru:
  ```bash
  uv run alembic revision --autogenerate -m "tambah kolom baru ke users"
  ```
* **Menjalankan Migrasi ke Database:**
  ```bash
  uv run alembic upgrade head
  ```
* **Membatalkan Migrasi Terakhir (Rollback):**
  ```bash
  uv run alembic downgrade -1
  ```

---

## 9. Pengujian (Testing)

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

## 10. Praktik Terbaik (Best Practices)

Saat Anda mengembangkan aplikasi menggunakan template FastIQ, harap ikuti aturan berikut:
1. **Terapkan Separation of Concerns:**
   * **Router:** Dilarang meletakkan logika bisnis atau pemanggilan database langsung. Router hanya bertugas menerima request, memanggil service, dan mengembalikan response sesuai skema.
   * **Service:** Seluruh aturan dan logika bisnis wajib ditulis di sini. Service memanggil Repository untuk mengambil/menyimpan data.
   * **Repository:** Lapisan yang berinteraksi langsung dengan database melalui ORM SQLAlchemy.
2. **Model Terpusat:**
   * Jangan meletakkan kelas SQLAlchemy Model di dalam modul bisnis. Letakkan semuanya di folder `app/models/` dan daftarkan di `app/models/__init__.py`. Hal ini penting agar Alembic dapat melacak seluruh relasi model dengan baik secara otomatis.
3. **Response Enveloping:**
   * Pastikan endpoint Anda mengembalikan skema response standar. Gunakan kelas `ApiResponse[T]` untuk data tunggal dan `ApiListResponse[T]` untuk data berbentuk list.
4. **Gunakan Exception Handler:**
   * Jangan menangani exception secara manual menggunakan blok try/except di Router demi mengembalikan JSON error manual. Cukup lemparkan instance subclass dari `AppException` (seperti `NotFoundException`, `BadRequestException`, `ForbiddenException`, dsb.) dari Service, dan sistem akan mengonversinya menjadi response API error standar secara otomatis.

---

## 11. Autentikasi & Keamanan (JWT Auth)

FastIQ mengimplementasikan sistem autentikasi berbasis JWT (JSON Web Token) dengan menggunakan pasangan Access Token (jangka pendek) dan Refresh Token (jangka panjang yang disimpan di database secara terenkripsi menggunakan SHA-256).

### A. Endpoints Autentikasi

Semua API endpoint autentikasi berada di bawah prefix `/api/auth`:

1. **Register User Baru**
   * **Endpoint:** `POST /api/auth/register`
   * **Request Body:**
     ```json
     {
       "email": "user@example.com",
       "password": "securepassword",
       "name": "John Doe"
     }
     ```
   * **Response:** Mengembalikan data user yang berhasil didaftarkan (`UserResponse`) terbungkus dalam `ApiResponse`.

2. **Login / Dapatkan Token**
   * **Endpoint:** `POST /api/auth/login`
   * **Request Body:**
     ```json
     {
       "email": "user@example.com",
       "password": "securepassword"
     }
     ```
   * **Response:** Mengembalikan `access_token`, `refresh_token`, `token_type`, dan `expires_in` terbungkus dalam `ApiResponse`.

3. **Refresh Access Token**
   * **Endpoint:** `POST /api/auth/refresh`
   * **Request Body:**
     ```json
     {
       "refresh_token": "string_refresh_token_di_sini"
     }
     ```
   * **Response:** Mengembalikan `access_token` baru beserta `refresh_token` baru (token rotation).

4. **Logout**
   * **Endpoint:** `POST /api/auth/logout`
   * **Request Body:**
     ```json
     {
       "refresh_token": "string_refresh_token_di_sini"
     }
     ```
   * **Response:** Merevokasi refresh token tersebut di database.

5. **Get Profil Saya (Protected)**
   * **Endpoint:** `GET /api/users/me`
   * **Header:** `Authorization: Bearer <access_token>`
   * **Response:** Mengembalikan profil user yang sedang login.

### B. Pola Proteksi Route (Protected Routes)

Untuk mengamankan route tertentu agar hanya dapat diakses oleh user yang telah terautentikasi, gunakan dependency `get_current_user` di level router:

```python
from fastapi import APIRouter, Depends
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/features")

@router.get("/protected-endpoint")
async def my_protected_route(
    current_user: User = Depends(get_current_user)
):
    return {"message": f"Hello, {current_user.name}"}
```

Jika token tidak dilampirkan, salah, atau kedaluwarsa, endpoint secara otomatis mengembalikan HTTP 401 (`UnauthorizedException`) dengan format response error terstandar:

```json
{
  "success": false,
  "message": "Invalid or expired token",
  "errors": []
}
```

---

## 12. FAQ (Frequently Asked Questions)

**T: Mengapa file SQLAlchemy Model tidak diletakkan di dalam modul bisnis (misalnya di `app/modules/users/models.py`)?**
J: Agar Alembic dapat melacak model database dengan mudah dan menghindari isu *circular imports* saat terdapat relasi *foreign key* antar model yang berbeda modul. Dengan meletakkannya di `app/models/`, pendaftaran model ke metadata SQLAlchemy menjadi tersentralisasi dan rapi.

**T: Bagaimana cara menambahkan modul bisnis baru?**
J: Anda hanya perlu membuat folder baru di `app/modules/<nama_modul>/` yang berisi `router.py`, `service.py`, `repository.py`, dan `schemas.py`. Definisikan model database baru Anda di `app/models/<nama_model>.py` dan daftarkan di `app/models/__init__.py`. Kemudian daftarkan router baru tersebut di `app/main.py`. Anda tidak perlu mengubah atau menyentuh berkas di folder `app/core/`.
