# FastIQ Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build FastIQ Phase 1 (Foundation) FastAPI starter kit with uv, asyncpg, Docker, logging, global error handling, and a users module CRUD demo.

**Architecture:** Router-Service-Repository pattern. Centralized models. Global exceptions, structured logging with request-id context middleware.

**Tech Stack:** FastAPI, SQLAlchemy 2.x (asyncpg), Alembic, Pydantic v2, Pydantic Settings, Uvicorn, Pytest, aiosqlite (for tests), uuid6 (for uuid7).

## Global Constraints
- Target Python version: 3.12+ (standard `pyproject.toml` config).
- All database operations are asynchronous using `AsyncSession`.
- All response envelopes must follow the `PRD.md §10` format.

---

### Task 1: Initialize Project & Setup Configuration

**Files:**
- Create: `pyproject.toml`
- Create: `app/__init__.py`
- Create: `app/config/settings.py`
- Create: `app/config/constants.py`
- Create: `.env.example`
- Create: `.env`

**Interfaces:**
- Produces: `app.config.settings.settings` instance.

- [ ] **Step 1: Write pyproject.toml**
Create `pyproject.toml` with dependencies: `fastapi`, `uvicorn[standard]`, `pydantic-settings`, `sqlalchemy[asyncio]`, `asyncpg`, `alembic`, `uuid6`, `passlib[bcrypt]`, `pytest`, `pytest-asyncio`, `aiosqlite`, `httpx`.

```toml
[project]
name = "fastiq"
version = "0.1.0"
description = "Opinionated FastAPI Project Template"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.111.0",
    "uvicorn[standard]>=0.30.0",
    "pydantic-settings>=2.3.0",
    "sqlalchemy[asyncio]>=2.0.30",
    "asyncpg>=0.29.0",
    "alembic>=1.13.1",
    "uuid6>=2024.7.10",
    "passlib[bcrypt]>=1.7.4",
]

[dependency-groups]
dev = [
    "pytest>=8.2.0",
    "pytest-asyncio>=0.23.0",
    "aiosqlite>=0.20.0",
    "httpx>=0.27.0",
]
```

- [ ] **Step 2: Sync dependencies via uv**
Run: `uv sync`
Expected: Resolves packages and writes `uv.lock`.

- [ ] **Step 3: Create .env.example**
Create `.env.example` file.

```env
APP_NAME=FastIQ
APP_ENV=development
DEBUG=true
PORT=8000
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/fastiq
SECRET_KEY=supersecretkeychangemeinproduction
```

- [ ] **Step 4: Copy .env.example to .env**
Run: `cp .env.example .env`

- [ ] **Step 5: Write app/config/settings.py**
Create `app/config/settings.py` using Pydantic Settings.

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    APP_NAME: str = "FastIQ"
    APP_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    DATABASE_URL: str
    SECRET_KEY: str

settings = Settings()
```

- [ ] **Step 6: Write app/config/constants.py**
Create empty constant mapping placeholder.

```python
# Constants for application
API_V1_PREFIX: str = "/api"
```

- [ ] **Step 7: Run settings validator test**
Run: `uv run python -c "from app.config.settings import settings; print(settings.APP_NAME)"`
Expected: Outputs `FastIQ`.

- [ ] **Step 8: Commit**
```bash
git add pyproject.toml uv.lock .env.example .env app/config/settings.py app/config/constants.py
git commit -m "feat: init project structure and configurations"
```

---

### Task 2: Standardized Responses, Pagination, and Exceptions

**Files:**
- Create: `app/core/responses.py`
- Create: `app/core/pagination.py`
- Create: `app/core/exceptions.py`

**Interfaces:**
- Produces: `ApiResponse`, `ApiListResponse` schemas.
- Produces: `AppException` and base exceptions.
- Produces: `register_exception_handlers` function to hook into FastAPI.

- [ ] **Step 1: Write app/core/responses.py**
Define standard Pydantic response models.

```python
from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel

T = TypeVar('T')

class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "Success"
    data: Optional[T] = None

class PaginationInfo(BaseModel):
    page: int
    per_page: int
    total: int
    total_pages: int

class ApiListResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "Success"
    data: list[T]
    pagination: PaginationInfo

class ErrorDetail(BaseModel):
    field: Optional[str] = None
    message: str

class ApiErrorResponse(BaseModel):
    success: bool = False
    message: str
    errors: Optional[list[ErrorDetail]] = None
```

- [ ] **Step 2: Write app/core/pagination.py**
Create helper to build pagination.

```python
import math
from app.core.responses import PaginationInfo

def build_pagination_info(page: int, per_page: int, total: int) -> PaginationInfo:
    total_pages = math.ceil(total / per_page) if total > 0 else 0
    return PaginationInfo(
        page=page,
        per_page=per_page,
        total=total,
        total_pages=total_pages
    )
```

- [ ] **Step 3: Write app/core/exceptions.py**
Define application exceptions and fastapi handler registrar.

```python
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.responses import ApiErrorResponse, ErrorDetail

class AppException(Exception):
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST, errors: list[ErrorDetail] = None):
        self.message = message
        self.status_code = status_code
        self.errors = errors
        super().__init__(message)

class NotFoundException(AppException):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=status.HTTP_404_NOT_FOUND)

class BadRequestException(AppException):
    def __init__(self, message: str = "Bad request"):
        super().__init__(message, status_code=status.HTTP_400_BAD_REQUEST)

def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content=ApiErrorResponse(
                success=False,
                message=exc.message,
                errors=exc.errors
            ).model_dump()
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        errors = [
            ErrorDetail(field=".".join(str(p) for p in err["loc"][1:]), message=err["msg"])
            for err in exc.errors()
        ]
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ApiErrorResponse(
                success=False,
                message="Validation Error",
                errors=errors
            ).model_dump()
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        # Fallback to general internal server error
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ApiErrorResponse(
                success=False,
                message="Internal Server Error"
            ).model_dump()
        )
```

- [ ] **Step 4: Commit**
```bash
git add app/core/responses.py app/core/pagination.py app/core/exceptions.py
git commit -m "feat: implement standard response structure and exception handlers"
```

---

### Task 3: Logger, Utilities, and Middleware Setup

**Files:**
- Create: `app/config/logger.py`
- Create: `app/core/middleware.py`
- Create: `app/utils/uuid.py`

**Interfaces:**
- Produces: `app.config.logger.setup_logging()` configurer.
- Produces: `RequestLoggingMiddleware` class.
- Produces: `generate_uuid7()` function returning standard string.

- [ ] **Step 1: Write app/utils/uuid.py**
Uuid7 standard generator.

```python
import uuid
from uuid6 import uuid7

def generate_uuid7() -> uuid.UUID:
    return uuid7()
```

- [ ] **Step 2: Write app/config/logger.py**
Setup dictionary-based logging with Request-ID format support.

```python
import logging
import logging.config
import os
from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")

class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_var.get()
        return True

def setup_logging():
    os.makedirs("logs", exist_ok=True)
    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "request_id": {
                "()": RequestIdFilter,
            }
        },
        "formatters": {
            "standard": {
                "format": "%(asctime)s [%(levelname)s] [%(request_id)s] %(message)s"
            },
        },
        "handlers": {
            "console": {
                "level": "INFO",
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "filters": ["request_id"],
            },
            "file": {
                "level": "INFO",
                "class": "logging.handlers.RotatingFileHandler",
                "filename": "logs/app.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "formatter": "standard",
                "filters": ["request_id"],
            }
        },
        "loggers": {
            "": {
                "handlers": ["console", "file"],
                "level": "INFO",
                "propagate": True
            }
        }
    }
    logging.config.dictConfig(log_config)
```

- [ ] **Step 3: Write app/core/middleware.py**
Add middleware for correlation request ID, logger timing, and custom metrics.

```python
import time
import logging
from uuid6 import uuid7
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.config.logger import request_id_var

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        req_id = request.headers.get("X-Request-ID") or str(uuid7())
        request_id_var.set(req_id)
        
        start_time = time.perf_counter()
        
        response = await call_next(request)
        
        duration = time.perf_counter() - start_time
        response.headers["X-Request-ID"] = req_id
        
        logger.info(
            f"Method: {request.method} | Path: {request.url.path} | "
            f"Duration: {duration:.4f}s | Status: {response.status_code}"
        )
        return response
```

- [ ] **Step 4: Run utility verification**
Run: `uv run python -c "from app.utils.uuid import generate_uuid7; print(generate_uuid7())"`
Expected: Prints a valid UUIDv7 string.

- [ ] **Step 5: Commit**
```bash
git add app/utils/uuid.py app/config/logger.py app/core/middleware.py
git commit -m "feat: add logging, middleware, and uuid utility"
```

---

### Task 4: Database Connection Setup (SQLAlchemy Async)

**Files:**
- Create: `app/config/database.py`

**Interfaces:**
- Produces: `Base` (SQLAlchemy DeclarativeBase).
- Produces: `async_session` (session maker instance).
- Produces: `get_db` dependency generator.

- [ ] **Step 1: Write app/config/database.py**
Async engine configuration.

```python
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.config.settings import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True
)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

- [ ] **Step 2: Commit**
```bash
git add app/config/database.py
git commit -m "feat: configure async sqlalchemy database connection"
```

---

### Task 5: Centralized User Model and Schemas

**Files:**
- Create: `app/models/__init__.py`
- Create: `app/models/user.py`
- Create: `app/modules/users/schemas.py`
- Create: `app/config/security.py`

**Interfaces:**
- Produces: `User` SQLAlchemy entity.
- Produces: Pydantic input/output schemas for Users module.
- Produces: `hash_password` utility.

- [ ] **Step 1: Write app/config/security.py**
Minimal password hashing via passlib bcrypt context.

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
```

- [ ] **Step 2: Write app/models/user.py**
Base models and mapping rules.

```python
import uuid
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.config.database import Base
from app.utils.uuid import generate_uuid7

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=generate_uuid7)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
```

- [ ] **Step 3: Write app/models/__init__.py**
Import models to populate `Base.metadata`.

```python
from app.config.database import Base
from app.models.user import User

__all__ = ["Base", "User"]
```

- [ ] **Step 4: Write app/modules/users/schemas.py**
Create API payload structures.

```python
import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    name: str = Field(min_length=2, max_length=255)

class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

- [ ] **Step 5: Verify models initialization**
Run: `uv run python -c "from app.models import Base; print(Base.metadata.tables.keys())"`
Expected: Prints `dict_keys(['users'])`.

- [ ] **Step 6: Commit**
```bash
git add app/config/security.py app/models/user.py app/models/__init__.py app/modules/users/schemas.py
git commit -m "feat: add user model, schemas, and password hashing utility"
```

---

### Task 6: Repository and Service Layers

**Files:**
- Create: `app/modules/users/repository.py`
- Create: `app/modules/users/service.py`

**Interfaces:**
- Produces: `UserRepository` class.
- Produces: `UserService` class.

- [ ] **Step 1: Write app/modules/users/repository.py**
Add data access handlers using select/scalars queries.

```python
import uuid
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User

class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user: User) -> User:
        self.db.add(user)
        await self.db.flush()
        return user

    async def find_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalars().first()

    async def find_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalars().first()

    async def list_all(self, offset: int, limit: int) -> list[User]:
        result = await self.db.execute(select(User).offset(offset).limit(limit))
        return list(result.scalars().all())

    async def count_all(self) -> int:
        result = await self.db.execute(select(func.count()).select_from(User))
        return result.scalar_one()
```

- [ ] **Step 2: Write app/modules/users/service.py**
Service interface containing core business actions and logic constraint evaluations.

```python
import uuid
from typing import Optional
from app.models.user import User
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import CreateUserRequest
from app.config.security import hash_password
from app.core.exceptions import BadRequestException, NotFoundException

class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    async def create_user(self, request: CreateUserRequest) -> User:
        existing = await self.repo.find_by_email(request.email)
        if existing:
            raise BadRequestException("Email already registered")
            
        hashed = hash_password(request.password)
        new_user = User(
            email=request.email,
            hashed_password=hashed,
            name=request.name
        )
        return await self.repo.create(new_user)

    async def get_user(self, user_id: uuid.UUID) -> User:
        user = await self.repo.find_by_id(user_id)
        if not user:
            raise NotFoundException("User not found")
        return user

    async def list_users(self, page: int, per_page: int) -> tuple[list[User], int]:
        offset = (page - 1) * per_page
        users = await self.repo.list_all(offset, per_page)
        total = await self.repo.count_all()
        return users, total
```

- [ ] **Step 3: Commit**
```bash
git add app/modules/users/repository.py app/modules/users/service.py
git commit -m "feat: add repository and service layers for users module"
```

---

### Task 7: Routing API Implementation & Root Handlers

**Files:**
- Create: `app/core/dependencies.py`
- Create: `app/modules/users/router.py`
- Create: `app/main.py`

**Interfaces:**
- Produces: FastAPI instance setup inside `app/main.py`.
- Produces: HTTP API Endpoints under `/api/users`.

- [ ] **Step 1: Write app/core/dependencies.py**
Dependency providers for service injection.

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.database import get_db
from app.modules.users.repository import UserRepository
from app.modules.users.service import UserService

def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)

def get_user_service(repo: UserRepository = Depends(get_user_repository)) -> UserService:
    return UserService(repo)
```

- [ ] **Step 2: Write app/modules/users/router.py**
Define request handling routes.

```python
import uuid
from fastapi import APIRouter, Depends, Query, status
from app.core.responses import ApiResponse, ApiListResponse
from app.core.pagination import build_pagination_info
from app.modules.users.schemas import CreateUserRequest, UserResponse
from app.modules.users.service import UserService
from app.core.dependencies import get_user_service

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("", response_model=ApiResponse[UserResponse], status_code=status.HTTP_201_CREATED)
async def create_user(
    request: CreateUserRequest,
    service: UserService = Depends(get_user_service)
):
    user = await service.create_user(request)
    return ApiResponse(
        success=True,
        message="User created successfully",
        data=UserResponse.model_validate(user)
    )

@router.get("/{user_id}", response_model=ApiResponse[UserResponse])
async def get_user(
    user_id: uuid.UUID,
    service: UserService = Depends(get_user_service)
):
    user = await service.get_user(user_id)
    return ApiResponse(
        success=True,
        message="User retrieved successfully",
        data=UserResponse.model_validate(user)
    )

@router.get("", response_model=ApiListResponse[UserResponse])
async def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    service: UserService = Depends(get_user_service)
):
    users, total = await service.list_users(page, per_page)
    data = [UserResponse.model_validate(u) for u in users]
    pagination = build_pagination_info(page, per_page, total)
    return ApiListResponse(
        success=True,
        message="Users listed successfully",
        data=data,
        pagination=pagination
    )
```

- [ ] **Step 3: Write app/main.py**
Wire components together. Expose a minimal `/health` response.

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.config.settings import settings
from app.config.logger import setup_logging
from app.core.exceptions import register_exception_handlers
from app.core.middleware import RequestLoggingMiddleware
from app.modules.users.router import router as users_router
from app.core.responses import ApiResponse

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup tasks
    setup_logging()
    yield
    # Shutdown tasks

app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan
)

# Middleware
app.add_middleware(RequestLoggingMiddleware)

# Exceptions
register_exception_handlers(app)

# Health endpoint
@app.get("/health", response_model=ApiResponse[dict[str, str]])
async def health_check():
    return ApiResponse(
        success=True,
        message="Service is healthy",
        data={"status": "ok"}
    )

# Routing
app.include_router(users_router, prefix="/api")
```

- [ ] **Step 4: Commit**
```bash
git add app/core/dependencies.py app/modules/users/router.py app/main.py
git commit -m "feat: implement router layer and root app configuration"
```

---

### Task 8: Database Seeder and Alembic Migration Setup

**Files:**
- Create: `app/scripts/seed.py`
- Create: `app/scripts/seeders/user_seeder.py`
- Modify: `alembic/env.py` (Created by alembic init)
- Create: `alembic.ini`

**Interfaces:**
- Produces: `python -m app.scripts.seed` seeder script.
- Produces: Alembic configuration capable of executing migrations.

- [ ] **Step 1: Setup Alembic files**
Run: `uv run alembic init alembic`
Expected: Creates `alembic/` directory and `alembic.ini` config.

- [ ] **Step 2: Modify alembic.ini**
Open `alembic.ini` and set postgres database URL dynamically or leave it to env variable handling in env.py. We'll read from `settings.DATABASE_URL` in `env.py`, so we can leave `sqlalchemy.url` placeholder empty.

```ini
# Edit alembic.ini line:
sqlalchemy.url = driver://user:pass@localhost/dbname
```

- [ ] **Step 3: Modify alembic/env.py**
Configure migration metadata to auto-discover models and read url from settings.

```python
# Replace alembic/env.py content with asyncpg standard env.py:
import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

# config
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import models metadata
from app.config.database import Base
from app.models import Base as ModelsBase
from app.config.settings import settings

target_metadata = ModelsBase.metadata

# Set database URL dynamically from app settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
```

- [ ] **Step 4: Write app/scripts/seeders/user_seeder.py**
Create async user seed helper.

```python
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.modules.users.repository import UserRepository
from app.config.security import hash_password

logger = logging.getLogger(__name__)

async def seed_users(db: AsyncSession) -> None:
    repo = UserRepository(db)
    
    # Check if we already have users
    total = await repo.count_all()
    if total > 0:
        logger.info("Database already seeded with users, skipping.")
        return
        
    admin_user = User(
        email="admin@fastiq.com",
        hashed_password=hash_password("adminpassword"),
        name="System Administrator"
    )
    await repo.create(admin_user)
    logger.info("User table seeded successfully.")
```

- [ ] **Step 5: Write app/scripts/seed.py**
Database seeding root router orchestrator.

```python
import asyncio
import logging
from app.config.database import async_session
from app.config.logger import setup_logging
from app.scripts.seeders.user_seeder import seed_users

logger = logging.getLogger(__name__)

async def main():
    setup_logging()
    logger.info("Starting database seed process...")
    async with async_session() as session:
        async with session.begin():
            await seed_users(session)
    logger.info("Database seeding completed.")

if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 6: Commit**
```bash
git add alembic.ini alembic/env.py alembic/script.py.mako app/scripts/seed.py app/scripts/seeders/user_seeder.py
git commit -m "feat: configure alembic and seeder modules"
```

---

### Task 9: Smoke Tests Scaffolding

**Files:**
- Create: `app/tests/__init__.py`
- Create: `app/tests/conftest.py`
- Create: `app/tests/test_users.py`

**Interfaces:**
- Produces: `pytest` runnable config override using SQLite in-memory test database.

- [ ] **Step 1: Write app/tests/conftest.py**
Setup overrides for database connections.

```python
import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.config.database import Base, get_db
from app.main import app
from httpx import AsyncClient, ASGITransport

# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

@pytest.fixture(scope="session")
def event_loop():
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
async def setup_db():
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Drop tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session

@pytest.fixture
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    # Override database dependency
    async def override_get_db():
        try:
            yield db
            await db.commit()
        except Exception:
            await db.rollback()
            raise

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
```

- [ ] **Step 2: Write app/tests/test_users.py**
Sanity-check API endpoints validation test suite.

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] == "ok"

@pytest.mark.asyncio
async def test_create_and_get_user(client: AsyncClient):
    # 1. Create User
    payload = {
        "email": "test@example.com",
        "password": "strongpassword",
        "name": "Test User"
    }
    response = await client.post("/api/users", json=payload)
    assert response.status_code == 201
    res_data = response.json()
    assert res_data["success"] is True
    user_id = res_data["data"]["id"]
    
    # 2. Get User by ID
    get_res = await client.get(f"/api/users/{user_id}")
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data["data"]["email"] == "test@example.com"
    assert get_data["data"]["name"] == "Test User"

    # 3. List Users
    list_res = await client.get("/api/users")
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["pagination"]["total"] == 1
    assert len(list_data["data"]) == 1
```

- [ ] **Step 3: Run Pytest**
Run: `uv run pytest app/tests/ -v`
Expected: 2 passed.

- [ ] **Step 4: Commit**
```bash
git add app/tests/__init__.py app/tests/conftest.py app/tests/test_users.py
git commit -m "test: add integration test suite scaffold and smoke tests"
```

---

### Task 10: Docker Setup for Development and Production

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.dev.yml`
- Create: `docker-compose.yml`
- Create: `.dockerignore`

**Interfaces:**
- Produces: Docker targets capable of spinning up Postgres and/or FastIQ runtime.

- [ ] **Step 1: Write .dockerignore**
Create dockerignore filter file.

```dockerignore
.git
.venv
__pycache__
*.pyc
*.pyo
*.pyd
.pytest_cache
logs/
alembic.ini
.env
.env.local
```

- [ ] **Step 2: Write Dockerfile**
Standard python production-grade multi-stage Docker build config.

```dockerfile
# Base stage for dependencies
FROM python:3.12-slim AS base

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/venv

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.11.23 /uv /uvx /bin/

# Install system dependencies needed for runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy configuration files
COPY pyproject.toml uv.lock ./

# Install dependencies without app code
RUN uv sync --frozen --no-install-project --no-dev

# Development stage
FROM base AS dev
RUN uv sync --frozen --no-install-project
COPY . .
CMD ["/venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production stage
FROM base AS prod
COPY . .
RUN uv sync --frozen

# Create a non-privileged user to run the app
RUN addgroup --system --gid 1001 appgroup && \
    adduser --system --uid 1001 --gid 1001 appuser
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["/venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 3: Write docker-compose.dev.yml**
Compose file for local development workspace.

```yaml
services:
  api:
    build:
      context: .
      target: dev
    ports:
      - "8000:8000"
    volumes:
      - .:/app
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/fastiq
      - APP_ENV=development
      - DEBUG=true
      - SECRET_KEY=devsecretkeychangeinproduction
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:17-alpine
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=fastiq
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d fastiq"]
      interval: 5s
      timeout: 5s
      retries: 5
```

- [ ] **Step 4: Write docker-compose.yml**
Standalone docker compose template optimized for production.

```yaml
services:
  api:
    build:
      context: .
      target: prod
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/fastiq
      - APP_ENV=production
      - DEBUG=false
      - SECRET_KEY=prodsecretkeychangeinproduction
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:17-alpine
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=fastiq
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d fastiq"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

- [ ] **Step 5: Test development container build**
Run: `docker compose -f docker-compose.dev.yml build api`
Expected: Clean build finishing with exit code 0.

- [ ] **Step 6: Commit**
```bash
git add .dockerignore Dockerfile docker-compose.dev.yml docker-compose.yml
git commit -m "feat: add Dockerfile and docker-compose configurations"
```

---

### Task 11: Readme & Verification

**Files:**
- Modify: `README.md`
- Modify: `CLAUDE.md` (Update test/run commands section now that they exist)

**Interfaces:**
- Produces: Completed `README.md` and up-to-date `CLAUDE.md`.

- [ ] **Step 1: Write README.md**
Fill `README.md` content documenting the stack, dev setup, migrations, seeders, docker, and directory layout.

```markdown
# FastIQ — Opinionated FastAPI Project Template

FastIQ adalah project template / starter kit opiniated untuk membangun REST API menggunakan FastAPI dengan arsitektur modular yang bersih (Router-Service-Repository).

## Tech Stack
- **Framework:** FastAPI + Uvicorn
- **Database:** SQLAlchemy 2.x (Async) + Alembic
- **Validation:** Pydantic v2 + Pydantic Settings
- **Dependency Manager:** uv
- **Testing:** Pytest

## Development Setup

### Prerequisite
Pastikan Anda sudah menginstall Python 3.12+ dan `uv`.

### Local Installation
1. Clone repositori ini.
2. Sinkronisasi dependency:
   ```bash
   uv sync
   ```
3. Copy environment configuration:
   ```bash
   cp .env.example .env
   ```

### Menjalankan Aplikasi
Jalankan dev server dengan hot reload:
```bash
uv run uvicorn app.main:app --reload
```
Akses API Docs di: http://localhost:8000/docs atau http://localhost:8000/redoc.

### Database Migrations (Alembic)
1. Generate migrasi baru secara otomatis:
   ```bash
   uv run alembic revision --autogenerate -m "Deskripsi revisi"
   ```
2. Jalankan migrasi ke database:
   ```bash
   uv run alembic upgrade head
   ```

### Seeding Database
Jalankan script seed untuk mengisi data awal:
```bash
uv run python -m app.scripts.seed
```

### Running Tests
Jalankan test suite menggunakan pytest:
```bash
uv run pytest app/tests/ -v
```

## Docker Support

### Development
Menjalankan workspace development (termasuk postgres) menggunakan Docker:
```bash
docker compose -f docker-compose.dev.yml up --build
```

### Production
Menjalankan build production yang teroptimasi:
```bash
docker compose up -d --build
```
Production image berjalan sebagai non-root user dan menyertakan health check otomatis.
```

- [ ] **Step 2: Update CLAUDE.md**
Modify `CLAUDE.md` with correct local testing and running commands now that we have settled on `uv`.

```markdown
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Running App
- Run local dev server: `uv run uvicorn app.main:app --reload`
- Healthcheck URL: `http://localhost:8000/health`
- API Docs: `http://localhost:8000/docs`

### Tests
- Run all tests: `uv run pytest app/tests/ -v`
- Run single test file: `uv run pytest app/tests/test_users.py -v`
- Run specific test: `uv run pytest app/tests/test_users.py::test_health_check -v`

### Database & Migrations
- Generate migration: `uv run alembic revision --autogenerate -m "description"`
- Apply migrations: `uv run alembic upgrade head`
- Rollback migration: `uv run alembic downgrade -1`
- Seed database: `uv run python -m app.scripts.seed`

### Docker
- Spin up dev stack: `docker compose -f docker-compose.dev.yml up --build`
- Spin up prod stack: `docker compose up -d --build`

## Architecture (per PRD.md §6-§9)

The core rule: **models are centralized, business logic is modularized.**

```
app/
├── main.py
├── config/         # settings.py, database.py, logger.py, security.py, constants.py
├── core/           # exceptions.py, responses.py, pagination.py, dependencies.py, enums.py, middleware.py
├── models/         # ALL SQLAlchemy ORM models live here (not inside modules) — keeps Alembic autodetect and cross-model relations simple
├── modules/        # one folder per business feature: users/, products/, orders/...
│   └── <feature>/
│       ├── router.py       # HTTP layer only — request in, validate, call service, return response. No business logic here.
│       ├── service.py      # business logic (create/update/login/register/etc.)
│       ├── repository.py   # all DB access (find_by_id, create, update, delete...)
│       └── schemas.py      # Pydantic request/response schemas for this module
├── scripts/        # seed.py, seeders/, commands.py
├── templates/      # Jinja templates, e.g. for emails (kept even though this is API-first)
└── tests/          # unit/, integration/, conftest.py
```

Strict separation of concerns: **router → service → repository**. Routers never touch the database or contain business rules; that's what makes new modules pluggable without touching core architecture (see PRD.md "Success Criteria").

## Conventions to enforce in generated code

- **Response envelope** — every endpoint returns this shape (PRD.md §10):
  - Success: `{"success": true, "message": "Success", "data": {...}}`
  - List: same plus `"pagination": {...}`
  - Error: `{"success": false, "message": "...", "errors": [{"field": "...", "message": "..."}]}`
- **Pagination** shape: `{"page", "per_page", "total", "total_pages"}` (PRD.md §11).
- **Exceptions are handled globally** (core/exceptions.py) — don't write per-endpoint try/except for validation, DB, not-found, auth, or 500 errors; add cases to the global handler instead.
- **Logging** is structured, includes request ID, method, path, duration, status; supports console + file output (PRD.md §13).
- **Security dependencies** (current user, role, optional permission checks) belong in `core/dependencies.py` / `config/security.py`, not scattered per-module.
- Adding a new business feature should only require adding a `modules/<name>/` folder (router/service/repository/schemas) — it should never require touching `core/`.
```

- [ ] **Step 3: Commit**
```bash
git add README.md CLAUDE.md
git commit -m "docs: finalize readme and update claude commands guide"
```
