# Product Requirements Document (PRD)

# FastIQ — Opinionated FastAPI Project Template

**Version:** 1.0
**Status:** Draft
**Owner:** PyArtisan / FastIQ
**Target:** Open Source Template

---

# 1. Overview

## Background

Saat ini sudah terdapat template **FlaskIQ** yang menyediakan struktur project opinionated untuk Flask.

Template baru akan dibuat menggunakan **FastAPI** dengan filosofi yang sama:

* Clean Architecture yang sederhana
* Modular based development
* Production Ready
* Developer Experience (DX) tinggi
* Mudah dipelajari
* Mudah di-scale

FastIQ **bukan framework baru**, tetapi sebuah **project template** yang menjadi starter kit untuk membangun REST API menggunakan FastAPI.

---

# 2. Goals

FastIQ bertujuan menyediakan template FastAPI yang memiliki:

* Clean project structure
* Standardized response
* Standardized logging
* Standardized error handling
* Service Layer pattern
* Repository pattern
* Modular feature architecture
* Docker ready
* Alembic migration ready
* Testing ready
* Security ready
* Seeder ready
* Production ready

---

# 3. Non Goals

FastIQ **tidak bertujuan** menyediakan:

* Admin Dashboard
* ORM Generator
* Code Generator
* Authentication Provider (OAuth Google dsb)
* Background Worker (Celery)
* Event Driven Architecture
* Microservice Framework

Semua dapat ditambahkan oleh developer sesuai kebutuhan.

---

# 4. Core Principles

## 1. Opinionated

Developer tidak perlu berpikir mengenai struktur project.

Semua mengikuti standar FastIQ.

---

## 2. Modular

Setiap business feature berada pada module masing-masing.

Contoh:

```
users/
products/
orders/
payments/
```

---

## 3. Separation of Concern

Business logic tidak boleh berada di Router.

Router hanya:

* menerima request
* validasi request
* memanggil service
* mengembalikan response

---

## 4. Production Ready

Template dapat langsung digunakan untuk production.

---

# 5. Tech Stack

## Backend

* FastAPI
* Uvicorn

## Database

* SQLAlchemy 2.x
* Alembic

## Validation

* Pydantic

## Configuration

* Pydantic Settings

## Authentication

* JWT

## Testing

* Pytest

## Logging

* Python Logging

## Documentation

* Swagger (OpenAPI)
* ReDoc

## Security
* Crypto
* UUIDv7

## Dependency

* Poetry atau uv (akan diputuskan)

---

# 6. Project Structure

Contoh struktur yang diusulkan:

```text
app/
│
├── main.py
│
├── config/
│   ├── settings.py
│   ├── database.py
│   ├── logger.py
│   ├── security.py
│   └── constants.py
│
├── core/
│   ├── exceptions.py
│   ├── responses.py
│   ├── pagination.py
│   ├── dependencies.py
│   ├── enums.py
│   └── middleware.py
│
├── models/
│   ├── user.py
│   ├── role.py
│   └── ...
│
├── modules/
│   ├── users/
│   │   │
│   │   ├── router.py
│   │   ├── service.py
│   │   ├── repository.py
│   │   ├── schemas.py (semua skema untuk Request, Response)
│   │   │
│   └── products/
│
├── scripts/
│   ├── seed.py
│   ├── seeders/
│   └── commands.py
│
├── templates/
│
├── tests/
│
└── utils/
```

---

# 7. Module Structure

Setiap module memiliki struktur berikut.

```
users/

router.py
service.py
repository.py
schemas.py
```

Penjelasan:

## router.py

Berisi:

* API Endpoint
* Dependency
* Inject Service

Tidak boleh ada business logic.

---

## schemas.py

Semua request schema.

Contoh

```
CreateUserRequest

UpdateUserRequest

LoginRequest
```


Semua response schema.

Contoh

```
UserResponse

LoginResponse

ProfileResponse
```

---

## service.py

Berisi business logic.

Contoh:

```
Create User

Update User

Login

Register

Reset Password
```

---

## repository.py

Semua komunikasi database.

Contoh

```
find_by_id()

find_by_email()

create()

update()

delete()
```

---

# 8. Models Folder

Semua ORM Model berada di folder

```
models/
```

Contoh

```
models/
    user.py
    role.py
    permission.py
```

Tidak berada di masing-masing module.

Tujuan:

* mudah digunakan Alembic
* relasi antar model lebih jelas

---

# 9. Configuration

Folder

```
config/
```

Berisi:

## settings.py

Menggunakan Pydantic Settings.

Membaca:

```
.env

.env.local

.env.production
```

---

## database.py

Membuat database connection.
Pastikan close connection setelah selesai.

---

## security.py

Berisi

* JWT
* Password Hash
* Secret Key
* Token Utilities

---

## logger.py

Konfigurasi logging.

---

## constants.py

Semua constant.

---

# 10. Response Standard

Seluruh endpoint wajib menggunakan format response yang sama.

## Success

```json
{
    "success": true,
    "message": "Success",
    "data": {}
}
```

---

## Success List

```json
{
    "success": true,
    "message": "Success",
    "data": [],
    "pagination": {}
}
```

---

## Error

```json
{
    "success": false,
    "message": "Validation Error",
    "errors": [
        {
            "field": "email",
            "message": "Email is required"
        }
    ]
}
```

---

# 11. Pagination Standard

```json
{
    "page": 1,
    "per_page": 10,
    "total": 100,
    "total_pages": 10
}
```

---

# 12. Exception Handling

Template menyediakan Global Exception Handler.

Menangani:

* Validation Error
* HTTP Exception
* Database Error
* Not Found
* Unauthorized
* Forbidden
* Internal Server Error

Developer tidak perlu menulis try/except di setiap endpoint.

---

# 13. Logging

Standard logging.

Mencatat:

* Request
* Response
* Exception
* SQL Error
* Startup
* Shutdown

Support:

Console

File

Format:

```
Timestamp

Level

Request ID

Method

Path

Duration

Status
```

---

# 14. Security

Template menyediakan:

JWT Authentication

Password Hash

Current User Dependency

Role Dependency

Permission Dependency (Optional)

Security Header

CORS

Trusted Host

Rate Limit (Optional)

---

# 15. Database Migration

Menggunakan

Alembic

Menyediakan command:

```
revision

upgrade

downgrade
```

Auto detect SQLAlchemy model.

---

# 16. Seeder

Folder

```
scripts/
```

Contoh

```
scripts/

seed.py

seeders/

user_seeder.py

role_seeder.py
```

Developer dapat menjalankan:

```
python scripts/seed.py
```

---

# 17. Testing

Menggunakan

Pytest

Struktur:

```
tests/

unit/

integration/

conftest.py
```

Target:

Repository Test

Service Test

API Test

---

# 18. Templates

Folder

```
templates/
```

Digunakan apabila project membutuhkan:

HTML

Email

Jinja Template

Walaupun fokus template adalah REST API, folder tetap disediakan.

---

# 19. Docker Support

## Development

```
docker-compose.dev.yml
```

Berisi

API

Postgres 17

Volume Mount

Hot Reload

---

## Production

```
docker-compose.yml
```

Menggunakan

Multi Stage Build

Non Root User

Health Check

Environment Variable

Optimized Image

---

# 20. Documentation

## README.md

Menjelaskan:

* Apa itu FastIQ
* Filosofi
* Fitur
* Requirement
* Installation
* Docker
* Environment
* Migration
* Seeder
* Menjalankan aplikasi
* Testing
* Project Structure
* Best Practice
* FAQ

---

## docs/architecture.md

Menjelaskan secara detail:

* Architecture Overview
* Folder Structure
* Request Flow
* Module Flow
* Dependency Injection
* Repository Pattern
* Service Layer
* Response Standard
* Exception Flow
* Logging Flow
* Authentication Flow
* Database Flow
* Alembic Flow
* Testing Strategy
* Best Practices

---

# 21. MVP Roadmap

## Phase 1 — Foundation

* Setup FastAPI project
* Configuration (`config/`)
* Database connection
* SQLAlchemy setup
* Alembic integration
* Docker (dev & prod)
* Basic logging
* Standard response
* Exception handler
* Base module example (`users`)

## Phase 2 — Developer Experience

* JWT authentication
* Security dependencies
* Pagination utilities
* Seeder framework
* Testing setup (Pytest)
* Environment management
* Request ID middleware
* Health check endpoint

## Phase 3 — Production Ready

* Comprehensive logging
* Docker optimization
* Role & permission support
* CI/CD example (GitHub Actions)
* Pre-commit hooks (formatting, linting)
* Sample modules (`auth`, `users`)
* Complete documentation (`README.md` dan `docs/architecture.md`)

---

# 22. Future Enhancements

Beberapa fitur yang dapat ditambahkan pada versi selanjutnya:

* CLI (`fastiq new`, `fastiq generate module`, dll.) sebagai bagian dari **PyArtisan**
* CRUD/module generator
* Multi-database support
* Async repository template
* Background tasks (Celery, RQ, Dramatiq)
* Caching (Redis)
* Event Bus
* Audit logging
* Multi-tenant architecture
* API versioning (`/api/v1`, `/api/v2`)
* OpenTelemetry (tracing & metrics)
* Kubernetes deployment manifests
* Built-in observability (Prometheus & Grafana)
* Hexagonal Architecture variant
* Domain-Driven Design (DDD) variant

---

## Success Criteria

FastIQ dianggap berhasil apabila memenuhi kriteria berikut:

* Struktur proyek konsisten dan mudah dipahami oleh developer baru.
* Seluruh endpoint mengikuti standar response dan error handling yang seragam.
* Penambahan module baru hanya membutuhkan pembuatan folder module (`router`, `request`, `response`, `service`, `repository`) tanpa mengubah arsitektur inti.
* Template dapat dijalankan secara lokal maupun di Docker (development dan production) dengan konfigurasi minimal.
* Mendukung migrasi database menggunakan Alembic dan proses seeding bawaan.
* Memiliki dokumentasi yang cukup sehingga developer dapat mulai mengembangkan fitur dalam waktu kurang dari 30 menit.
* Menjadi fondasi yang nantinya dapat diintegrasikan dengan **PyArtisan CLI** untuk menghasilkan proyek FastAPI secara otomatis, serupa dengan konsep **FlaskIQ** namun dengan arsitektur yang disesuaikan untuk FastAPI.
