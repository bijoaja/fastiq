# FastIQ Architecture

> **Language:** English | [Indonesian](../id/ARCHITECTURE.md)

Philosophy, project structure, database migrations, and best practices.

---

## 1. Philosophy & Core Principles

FastIQ is a project template (starter kit) built with **FastAPI**, designed to accelerate the development of production-ready REST APIs with clean, modular, and well-structured architecture. FastIQ is inspired by **FlaskIQ's** philosophy and tailored to enforce strict code cleanliness and separation of concerns.

FastIQ is built on several core principles:
1. **Opinionated:** Project structure is clearly defined. Developers don't need to worry about choosing directory layout, file naming, or config file location.
2. **Modular:** Each business feature is grouped into its own module (e.g., `users`, `products`, `orders`), making it easy to scale and maintain independently.
3. **Separation of Concerns:** Routers serve only as the HTTP layer (receive input, validate schema, call service, return response). Business logic lives in the **Service** layer, while database interactions are handled by the **Repository** layer (Router → Service → Repository).
4. **Production Ready:** Includes structured logging, global error handling, request ID tracking, standardized response schemas, async database integration, database migrations via Alembic, testing via Pytest, and Docker configuration (development & production).

### What FastIQ Does NOT Provide (Non-Goals)
FastIQ is intentionally minimal and focused. Therefore, FastIQ deliberately **does not provide**:
* Admin Dashboard
* ORM Generator & automatic Code Generator
* Third-Party Authentication providers (e.g., OAuth Google)
* Background Workers (e.g., Celery/Redis Queue)
* Event-Driven Architecture or Microservices frameworks

All of the above features can be added independently by developers according to their project needs.

---

## 2. Project Structure

FastIQ's project structure is designed to be modular and easy to understand:

```text
fastiq/
├── alembic/                # Database migration config & version files
├── app/
│   ├── config/             # Application settings, database, logging, & constants
│   │   ├── constants.py    # Application constants
│   │   ├── database.py     # SQLAlchemy Async Engine & Session setup
│   │   ├── logger.py       # Structured logging config (Console & File)
│   │   ├── security.py     # Encryption & security utilities (JWT, hashing)
│   │   └── settings.py     # Pydantic Settings-based application config
│   ├── core/               # Core application components
│   │   ├── dependencies.py # Dependency Injection (repository, service)
│   │   ├── exceptions.py   # Global Exception Handler & Custom Exceptions
│   │   ├── middleware.py   # Middleware such as RequestLogging (Request ID)
│   │   ├── pagination.py   # Pagination standardization helper
│   │   └── responses.py    # Standard API Response schemas (ApiResponse, ApiErrorResponse)
│   ├── models/             # ALL SQLAlchemy ORM models (centralized for Alembic)
│   │   └── user.py         # User model
│   ├── modules/            # Business feature modules (one subfolder per module)
│   │   ├── auth/           # Authentication Module (JWT)
│   │   │   ├── repository.py # Database operations for refresh tokens
│   │   │   ├── router.py   # API Endpoints (Register, Login, Refresh, Logout)
│   │   │   ├── schemas.py  # Authentication request & response schemas
│   │   │   └── service.py  # Authentication business logic & token management
│   │   └── users/          # Users Module
│   │       ├── repository.py # Users module-specific database operations
│   │       ├── router.py   # API Endpoints (HTTP Layer only, logic-free)
│   │       ├── schemas.py  # Pydantic request & response validation schemas
│   │       └── service.py  # Users module core business logic
│   ├── scripts/            # Helper scripts (e.g., seeder)
│   │   ├── seed.py         # Database seeding runner
│   │   └── seeders/        # Per-table/module seeders
│   ├── templates/          # Jinja templates folder (e.g., email templates)
│   ├── utils/              # Common helpers and utilities (e.g., UUID generator)
│   └── main.py             # FastAPI application entrypoint (router & middleware registration)
├── docs/                   # Project documentation (en/ and id/); docs/superpowers/ contains specs and plans
├── tests/                  # Unit & integration tests using Pytest
├── Dockerfile              # Multi-stage Dockerfile (targets: base, dev, prod)
├── docker-compose.dev.yml  # Development compose configuration
├── docker-compose.yml      # Production compose configuration
├── pyproject.toml          # Dependency definitions & testing config
└── uv.lock                 # Python dependencies lockfile
```

---

## 3. Database Migrations (Alembic)

Whenever you make changes to SQLAlchemy models in the `app/models/` folder, you must create a new migration version file.

* **Creating a New Migration File (Auto-generate):**
  Alembic will automatically compare your models against the current database state and create a new migration file:
  ```bash
  uv run alembic revision --autogenerate -m "add new column to users"
  ```
* **Running Migrations to Database:**
  ```bash
  uv run alembic upgrade head
  ```
* **Rolling Back the Last Migration:**
  ```bash
  uv run alembic downgrade -1
  ```

---

## 4. Best Practices

When developing applications using FastIQ, please follow these rules:
1. **Enforce Separation of Concerns:**
   * **Router:** Never place business logic or direct database calls. Routers only receive requests, call services, and return responses per schema.
   * **Service:** All business rules and logic must be written here. Service calls Repository to fetch/store data.
   * **Repository:** The layer that directly interacts with the database through SQLAlchemy ORM.
2. **Centralized Models:**
   * Don't place SQLAlchemy Model classes inside business modules. Place all of them in the `app/models/` folder and register in `app/models/__init__.py`. This is important so Alembic can properly track all model relationships automatically.
3. **Response Enveloping:**
   * Ensure your endpoints return standardized response schemas. Use the `ApiResponse[T]` class for single data and `ApiListResponse[T]` for list data.
4. **Use Exception Handler:**
   * Don't handle exceptions manually using try/except blocks in Router to return custom JSON errors. Simply raise instances of `AppException` subclasses (like `NotFoundException`, `BadRequestException`, `ForbiddenException`, etc.) from Service, and the system will automatically convert them to standardized API error responses.
