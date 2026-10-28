# Product Requirements Document (PRD)

# FastIQ — Opinionated FastAPI Project Template

**Version:** 1.0
**Status:** Draft
**Owner:** PyArtisan / FastIQ
**Target:** Open Source Template

---

# 1. Overview

## Background

Currently, a **FlaskIQ** template exists that provides an opinionated project structure for Flask.

A new template will be created using **FastAPI** with the same philosophy:

* Simple Clean Architecture
* Modular based development
* Production Ready
* High Developer Experience (DX)
* Easy to learn
* Easy to scale

FastIQ **is not a new framework**, but a **project template** that serves as a starter kit for building REST APIs using FastAPI.

---

# 2. Goals

FastIQ aims to provide a FastAPI template that has:

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

FastIQ **does not aim** to provide:

* Admin Dashboard
* ORM Generator
* Code Generator
* Authentication Provider (OAuth Google, etc.)
* Background Worker (Celery)
* Event Driven Architecture
* Microservice Framework

All of these can be added by developers according to their needs.

---

# 4. Core Principles

## 1. Opinionated

Developers do not need to think about project structure.

Everything follows FastIQ standards.

---

## 2. Modular

Each business feature lives in its own module.

Example:

```
users/
products/
orders/
payments/
```

---

## 3. Separation of Concern

Business logic must not be in the Router.

Router only:

* receives requests
* validates requests
* calls services
* returns responses

---

## 4. Production Ready

The template can be used directly for production.

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

* uv

---

# 6. Project Structure

Proposed structure example:

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
│   │   ├── schemas.py (all schemas for Request, Response)
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

Each module has the following structure:

```
users/

router.py
service.py
repository.py
schemas.py
```

Explanation:

## router.py

Contains:

* API Endpoints
* Dependency
* Service Injection

No business logic allowed.

---

## schemas.py

All request schemas.

Example:

```
CreateUserRequest

UpdateUserRequest

LoginRequest
```

All response schemas.

Example:

```
UserResponse

LoginResponse

ProfileResponse
```

---

## service.py

Contains business logic.

Example:

```
Create User

Update User

Login

Register

Reset Password
```

---

## repository.py

All database communication.

Example:

```
find_by_id()

find_by_email()

create()

update()

delete()
```

---

# 8. Models Folder

All ORM Models are in the folder:

```
models/
```

Example:

```
models/
    user.py
    role.py
    permission.py
```

Not in each module.

Purpose:

* easy for Alembic to use
* model relationships are clearer

---

# 9. Configuration

Folder:

```
config/
```

Contains:

## settings.py

Uses Pydantic Settings.

Reads:

```
.env

.env.local

.env.production
```

---

## database.py

Creates database connection.
Ensure connection is closed after use.

---

## security.py

Contains:

* JWT
* Password Hash
* Secret Key
* Token Utilities

---

## logger.py

Logging configuration.

---

## constants.py

All constants.

---

# 10. Response Standard

All endpoints must use the same response format.

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

The template provides a Global Exception Handler.

Handles:

* Validation Error
* HTTP Exception
* Database Error
* Not Found
* Unauthorized
* Forbidden
* Internal Server Error

Developers do not need to write try/except at every endpoint.

---

# 13. Logging

Standard logging.

Records:

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

The template provides:

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

Uses:

Alembic

Provides commands:

```
revision

upgrade

downgrade
```

Auto detect SQLAlchemy models.

---

# 16. Seeder

Folder:

```
scripts/
```

Example:

```
scripts/

seed.py

seeders/

user_seeder.py

role_seeder.py
```

Developers can run:

```
python scripts/seed.py
```

---

# 17. Testing

Uses:

Pytest

Structure:

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

Folder:

```
templates/
```

Used when the project needs:

HTML

Email

Jinja Template

Although the focus of the template is REST API, the folder is still provided.

---

# 19. Docker Support

## Development

```
docker-compose.dev.yml
```

Contains:

API

Postgres 17

Volume Mount

Hot Reload

---

## Production

```
docker-compose.yml
```

Uses:

Multi Stage Build

Non Root User

Health Check

Environment Variable

Optimized Image

---

# 20. Documentation

## README.md

Explains:

* What is FastIQ
* Philosophy
* Features
* Requirements
* Installation
* Docker
* Environment
* Migration
* Seeder
* Running the application
* Testing
* Project Structure
* Best Practices
* FAQ

---

## docs/architecture.md

Explains in detail:

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
* Complete documentation (`README.md` and `docs/architecture.md`)

---

# 22. Future Enhancements

Some features that can be added in future versions:

* CLI (`fastiq new`, `fastiq generate module`, etc.) as part of **PyArtisan**
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

FastIQ is considered successful if it meets the following criteria:

* Project structure is consistent and easy for new developers to understand.
* All endpoints follow uniform response and error handling standards.
* Adding a new module only requires creating a module folder (`router`, `request`, `response`, `service`, `repository`) without changing the core architecture.
* The template can run locally and in Docker (development and production) with minimal configuration.
* Supports database migrations using Alembic and built-in seeding process.
* Has sufficient documentation so developers can start developing features in less than 30 minutes.
* Serves as a foundation that can later be integrated with **PyArtisan CLI** to generate FastAPI projects automatically, similar to the **FlaskIQ** concept but with architecture adapted for FastAPI.
