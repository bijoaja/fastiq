# Arsitektur FastIQ

> **Bahasa:** Indonesia | [English](../en/ARCHITECTURE.md)

Filosofi, struktur proyek, migrasi database, dan praktik terbaik.

---

## 1. Filosofi & Prinsip Utama

FastIQ adalah sebuah template proyek (starter kit) berbasis **FastAPI** yang dirancang untuk mempercepat pembuatan REST API siap produksi dengan arsitektur yang bersih, modular, dan terstruktur dengan baik. FastIQ terinspirasi dari filosofi **FlaskIQ** dan dirancang khusus untuk memenuhi standar kebersihan kode dan pemisahan tanggung jawab (*Separation of Concerns*) yang ketat.

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

## 2. Struktur Proyek

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
├── docs/                   # Dokumentasi proyek (en/ dan id/); docs/superpowers/ berisi spec dan plan
├── tests/                  # File pengujian unit & integrasi menggunakan Pytest
├── Dockerfile              # Dockerfile Multi-stage (target: base, dev, prod)
├── docker-compose.dev.yml  # Compose development
├── docker-compose.yml      # Compose production
├── pyproject.toml          # Definisi dependensi & konfigurasi testing
└── uv.lock                 # Lockfile dependensi python
```

---

## 3. Database Migrasi (Alembic)

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

## 4. Praktik Terbaik (Best Practices)

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
