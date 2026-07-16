# FastIQ Phase 2 (JWT Authentication) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add JWT authentication (register, login, DB-backed rotating refresh token, logout) and a reusable `get_current_user` dependency to FastIQ.

**Architecture:** New `app/modules/auth/` module (router → service → repository, matching the `users` module pattern). Access tokens are stateless JWTs (PyJWT, HS256); refresh tokens are opaque random strings, stored only as SHA-256 hashes in a new `refresh_tokens` table, rotated (revoked + reissued) on every use.

**Tech Stack:** PyJWT (new dependency), existing FastAPI/SQLAlchemy 2.x async/Alembic/Pytest stack.

## Global Constraints

- Target Python >= 3.12, `uv` only (no Poetry) — matches existing `pyproject.toml`.
- All database operations use `AsyncSession` (SQLAlchemy 2.x async) — see `app/config/database.py`.
- Response envelope: success `ApiResponse[T]` (`success`, `message`, `data`), errors via `AppException` subclasses in `app/core/exceptions.py` — no per-endpoint try/except.
- Models live centrally in `app/models/`, never inside a module folder.
- IDs use `generate_uuid7()` from `app/utils/uuid.py`.
- `AppException` subclasses available: `NotFoundException` (404), `BadRequestException` (400), `UnauthorizedException` (401), `ForbiddenException` (403), `ConflictException` (409) — all in `app/core/exceptions.py`.
- Access token expiry: 15 minutes. Refresh token expiry: 7 days. JWT algorithm: HS256, signed with existing `settings.SECRET_KEY`.
- Refresh tokens are rotating: every `/auth/refresh` call revokes the presented token and issues a new pair. Reusing a revoked/expired/unknown token is rejected with `UnauthorizedException`.
- Out of scope: role/permission dependencies, seeder framework generalization, pagination utility enhancements, rate limiting, logout-all-devices.

---

### Task 1: Add PyJWT dependency, JWT settings, and token security helpers

**Files:**
- Modify: `pyproject.toml`
- Modify: `app/config/settings.py`
- Modify: `app/config/security.py`
- Test: `tests/test_security_tokens.py`

**Interfaces:**
- Produces: `settings.ACCESS_TOKEN_EXPIRE_MINUTES: int`, `settings.REFRESH_TOKEN_EXPIRE_DAYS: int`, `settings.JWT_ALGORITHM: str`.
- Produces: `create_access_token(user_id: uuid.UUID) -> str`, `decode_access_token(token: str) -> dict`, `generate_refresh_token() -> str`, `hash_token(token: str) -> str` in `app/config/security.py`.
- Consumes: `settings.SECRET_KEY` (existing), `UnauthorizedException` from `app/core/exceptions.py` (existing).

- [ ] **Step 1: Add PyJWT to pyproject.toml**

Edit `pyproject.toml`, add to the `dependencies` list (after `"email-validator>=2.0.0",`):

```toml
    "pyjwt>=2.8.0",
```

- [ ] **Step 2: Sync dependencies**

Run: `uv sync`
Expected: Resolves and installs `pyjwt`, updates `uv.lock`.

- [ ] **Step 3: Add JWT settings fields**

Edit `app/config/settings.py`. Current content:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "FastIQ"
    APP_ENV: str = "local"
    DEBUG: bool = True
    PORT: int = 8000
    DATABASE_URL: str
    SECRET_KEY: str

    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local", ".env.production"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()
```

Replace with:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "FastIQ"
    APP_ENV: str = "local"
    DEBUG: bool = True
    PORT: int = 8000
    DATABASE_URL: str
    SECRET_KEY: str

    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local", ".env.production"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()
```

- [ ] **Step 4: Write the failing test for token helpers**

Create `tests/test_security_tokens.py`:

```python
import uuid
import time
import pytest
import jwt
from app.config.settings import settings
from app.config.security import (
    create_access_token,
    decode_access_token,
    generate_refresh_token,
    hash_token,
)
from app.core.exceptions import UnauthorizedException

def test_create_and_decode_access_token():
    user_id = uuid.uuid4()
    token = create_access_token(user_id)
    payload = decode_access_token(token)
    assert payload["sub"] == str(user_id)

def test_decode_access_token_invalid_signature_raises():
    bad_token = jwt.encode({"sub": "x"}, "wrong-secret", algorithm=settings.JWT_ALGORITHM)
    with pytest.raises(UnauthorizedException):
        decode_access_token(bad_token)

def test_decode_access_token_expired_raises():
    expired_payload = {"sub": "x", "exp": int(time.time()) - 10}
    expired_token = jwt.encode(expired_payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    with pytest.raises(UnauthorizedException):
        decode_access_token(expired_token)

def test_generate_refresh_token_is_random_and_urlsafe():
    token_a = generate_refresh_token()
    token_b = generate_refresh_token()
    assert token_a != token_b
    assert len(token_a) > 20

def test_hash_token_is_deterministic_sha256_hex():
    token = "sample-token-value"
    digest = hash_token(token)
    assert len(digest) == 64
    assert digest == hash_token(token)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_security_tokens.py -v`
Expected: FAIL with `ImportError: cannot import name 'create_access_token'`

- [ ] **Step 3: Implement token helpers**

Edit `app/config/security.py`. Current content:

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash plain password using bcrypt."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against hashed password."""
    return pwd_context.verify(plain_password, hashed_password)
```

Replace with:

```python
import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from app.config.settings import settings
from app.core.exceptions import UnauthorizedException

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash plain password using bcrypt."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(user_id: uuid.UUID) -> str:
    """Create a short-lived signed JWT access token for the given user."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def decode_access_token(token: str) -> dict:
    """Decode and verify a JWT access token. Raises UnauthorizedException if invalid or expired."""
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except jwt.PyJWTError:
        raise UnauthorizedException("Invalid or expired token")

def generate_refresh_token() -> str:
    """Generate an opaque, URL-safe random refresh token."""
    return secrets.token_urlsafe(32)

def hash_token(token: str) -> str:
    """Hash a refresh token for storage (never store the raw token)."""
    return hashlib.sha256(token.encode()).hexdigest()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_security_tokens.py -v`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml uv.lock app/config/settings.py app/config/security.py tests/test_security_tokens.py
git commit -m "feat: add pyjwt dependency and access/refresh token security helpers

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 2: RefreshToken model and Alembic migration

**Files:**
- Create: `app/models/refresh_token.py`
- Modify: `app/models/__init__.py`
- Test: `tests/test_refresh_token_model.py`

**Interfaces:**
- Consumes: `Base` from `app.config.database`, `generate_uuid7` from `app.utils.uuid` (existing, see `app/models/user.py` for the pattern).
- Produces: `RefreshToken` model with fields `id`, `user_id`, `token_hash`, `expires_at`, `revoked_at`, `created_at`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_refresh_token_model.py`:

```python
import uuid
from datetime import datetime, timezone
from app.models.refresh_token import RefreshToken

def test_refresh_token_model_fields():
    user_id = uuid.uuid4()
    token = RefreshToken(
        user_id=user_id,
        token_hash="a" * 64,
        expires_at=datetime.now(timezone.utc),
    )
    assert token.user_id == user_id
    assert token.token_hash == "a" * 64
    assert token.revoked_at is None
    assert RefreshToken.__tablename__ == "refresh_tokens"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_refresh_token_model.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.models.refresh_token'`

- [ ] **Step 3: Implement RefreshToken model**

Create `app/models/refresh_token.py`:

```python
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column
from app.config.database import Base
from app.utils.uuid import generate_uuid7

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=generate_uuid7,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    token_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        nullable=False,
    )
```

- [ ] **Step 4: Register model centrally**

Edit `app/models/__init__.py`. Read the current file first, then add the import and `__all__` entry for `RefreshToken` alongside the existing `User` import (keep the exact style already used there — import `RefreshToken` from `app.models.refresh_token` and add `"RefreshToken"` to `__all__`).

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/test_refresh_token_model.py -v`
Expected: PASS (1 passed)

- [ ] **Step 6: Generate Alembic migration**

Start a local Postgres so autogenerate can connect:

```bash
docker compose -f docker-compose.dev.yml up -d db
until [ "$(docker inspect --format='{{json .State.Health.Status}}' fastiq-db-1)" = "\"healthy\"" ]; do sleep 1; done
uv run alembic revision --autogenerate -m "Add refresh tokens table"
docker compose -f docker-compose.dev.yml down
```

Expected: A new file appears under `alembic/versions/` containing `op.create_table('refresh_tokens', ...)` with a foreign key to `users.id`. Inspect the generated file to confirm it detected the table before proceeding.

- [ ] **Step 7: Commit**

```bash
git add app/models/refresh_token.py app/models/__init__.py tests/test_refresh_token_model.py alembic/versions/
git commit -m "feat: add RefreshToken model and initial migration

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 3: AuthRepository

**Files:**
- Create: `app/modules/auth/__init__.py` (empty)
- Create: `app/modules/auth/repository.py`
- Test: `tests/test_auth_repository.py`

**Interfaces:**
- Consumes: `RefreshToken` from `app.models.refresh_token` (Task 2), `AsyncSession` from `sqlalchemy.ext.asyncio`.
- Produces: `AuthRepository` class with `create_refresh_token(user_id: uuid.UUID, token_hash: str, expires_at: datetime) -> RefreshToken`, `find_valid_by_hash(token_hash: str) -> Optional[RefreshToken]`, `revoke(refresh_token: RefreshToken) -> None`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_auth_repository.py` (uses the `db` fixture from `tests/conftest.py`, same pattern as `tests/test_users_service.py`'s repository tests but against the real in-memory test DB rather than mocks, matching `tests/test_seeder.py`'s style):

```python
import uuid
from datetime import datetime, timedelta, timezone
import pytest
from app.modules.auth.repository import AuthRepository

@pytest.mark.asyncio
async def test_create_and_find_valid_refresh_token(db):
    repo = AuthRepository(db)
    user_id = uuid.uuid4()
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    created = await repo.create_refresh_token(user_id, "hash123", expires_at)
    assert created.token_hash == "hash123"

    found = await repo.find_valid_by_hash("hash123")
    assert found is not None
    assert found.id == created.id

@pytest.mark.asyncio
async def test_find_valid_by_hash_returns_none_for_unknown_hash(db):
    repo = AuthRepository(db)
    result = await repo.find_valid_by_hash("does-not-exist")
    assert result is None

@pytest.mark.asyncio
async def test_find_valid_by_hash_excludes_revoked(db):
    repo = AuthRepository(db)
    user_id = uuid.uuid4()
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    token = await repo.create_refresh_token(user_id, "hash456", expires_at)

    await repo.revoke(token)

    result = await repo.find_valid_by_hash("hash456")
    assert result is None

@pytest.mark.asyncio
async def test_find_valid_by_hash_excludes_expired(db):
    repo = AuthRepository(db)
    user_id = uuid.uuid4()
    expired_at = datetime.now(timezone.utc) - timedelta(days=1)
    await repo.create_refresh_token(user_id, "hash789", expired_at)

    result = await repo.find_valid_by_hash("hash789")
    assert result is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_auth_repository.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.modules.auth.repository'`

- [ ] **Step 3: Implement AuthRepository**

Create `app/modules/auth/__init__.py` (empty file).

Create `app/modules/auth/repository.py`:

```python
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.refresh_token import RefreshToken

class AuthRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_refresh_token(
        self, user_id: uuid.UUID, token_hash: str, expires_at: datetime
    ) -> RefreshToken:
        refresh_token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.db.add(refresh_token)
        await self.db.flush()
        return refresh_token

    async def find_valid_by_hash(self, token_hash: str) -> Optional[RefreshToken]:
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked_at.is_(None),
                RefreshToken.expires_at > func.now(),
            )
        )
        return result.scalars().first()

    async def revoke(self, refresh_token: RefreshToken) -> None:
        refresh_token.revoked_at = datetime.now(timezone.utc)
        await self.db.flush()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_auth_repository.py -v`
Expected: PASS (4 passed)

Note: if `test_find_valid_by_hash_excludes_expired` fails because SQLite compares `func.now()` differently than Postgres, replace the `expires_at > func.now()` filter's test expectation is still correct (SQLite's `now()` support via SQLAlchemy works for this comparison) — if it fails, check the actual error before changing the query; this is the same comparison style already proven to work against SQLite in `tests/test_seeder.py`.

- [ ] **Step 5: Commit**

```bash
git add app/modules/auth/__init__.py app/modules/auth/repository.py tests/test_auth_repository.py
git commit -m "feat: implement AuthRepository for refresh token persistence

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 4: Auth schemas

**Files:**
- Create: `app/modules/auth/schemas.py`
- Test: `tests/test_auth_schemas.py`

**Interfaces:**
- Consumes: nothing new (pure Pydantic schemas).
- Produces: `LoginRequest`, `TokenResponse`, `RefreshRequest`, `LogoutRequest` schemas for use in Task 5 (service) and Task 6 (router).

- [ ] **Step 1: Write the failing test**

Create `tests/test_auth_schemas.py`:

```python
import pytest
from pydantic import ValidationError
from app.modules.auth.schemas import LoginRequest, TokenResponse, RefreshRequest, LogoutRequest

def test_login_request_valid():
    req = LoginRequest(email="user@example.com", password="secret123")
    assert req.email == "user@example.com"

def test_login_request_invalid_email():
    with pytest.raises(ValidationError):
        LoginRequest(email="not-an-email", password="secret123")

def test_token_response_defaults():
    resp = TokenResponse(access_token="a", refresh_token="b", expires_in=900)
    assert resp.token_type == "bearer"
    assert resp.access_token == "a"
    assert resp.refresh_token == "b"
    assert resp.expires_in == 900

def test_refresh_request_valid():
    req = RefreshRequest(refresh_token="some-token")
    assert req.refresh_token == "some-token"

def test_logout_request_valid():
    req = LogoutRequest(refresh_token="some-token")
    assert req.refresh_token == "some-token"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_auth_schemas.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.modules.auth.schemas'`

- [ ] **Step 3: Implement schemas**

Create `app/modules/auth/schemas.py`:

```python
from pydantic import BaseModel, EmailStr, Field

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class RefreshRequest(BaseModel):
    refresh_token: str

class LogoutRequest(BaseModel):
    refresh_token: str
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_auth_schemas.py -v`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
git add app/modules/auth/schemas.py tests/test_auth_schemas.py
git commit -m "feat: add auth module request/response schemas

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 5: AuthService

**Files:**
- Create: `app/modules/auth/service.py`
- Test: `tests/test_auth_service.py`

**Interfaces:**
- Consumes: `UserRepository` (`app.modules.users.repository`, existing — has `find_by_email`, `create`), `UserService` (`app.modules.users.service`, existing — `create_user(request: CreateUserRequest) -> User`), `CreateUserRequest`/`UserResponse` (`app.modules.users.schemas`, existing), `AuthRepository` (Task 3), `LoginRequest`/`TokenResponse` (Task 4), `create_access_token`/`generate_refresh_token`/`hash_token`/`verify_password` (Task 1, `app.config.security`), `settings.REFRESH_TOKEN_EXPIRE_DAYS`/`settings.ACCESS_TOKEN_EXPIRE_MINUTES` (Task 1), `UnauthorizedException` (`app.core.exceptions`, existing).
- Produces: `AuthService` class with `register(request: CreateUserRequest) -> User`, `login(request: LoginRequest) -> TokenResponse`, `refresh(refresh_token: str) -> TokenResponse`, `logout(refresh_token: str) -> None`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_auth_service.py` (mock-based, same style as `tests/test_users_service.py`):

```python
import uuid
from datetime import datetime, timezone
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.core.exceptions import UnauthorizedException
from app.config.security import hash_password
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.modules.auth.schemas import LoginRequest
from app.modules.auth.service import AuthService
from app.modules.users.schemas import CreateUserRequest

@pytest.fixture
def mock_user_repo():
    return MagicMock()

@pytest.fixture
def mock_auth_repo():
    return MagicMock()

@pytest.fixture
def auth_service(mock_user_repo, mock_auth_repo):
    return AuthService(user_repo=mock_user_repo, auth_repo=mock_auth_repo)

@pytest.mark.asyncio
async def test_register_delegates_to_user_service(auth_service, mock_user_repo):
    mock_user_repo.find_by_email = AsyncMock(return_value=None)
    created_user = User(email="new@example.com", name="New", hashed_password="hashed")
    mock_user_repo.create = AsyncMock(return_value=created_user)

    request = CreateUserRequest(email="new@example.com", name="New", password="password123")
    result = await auth_service.register(request)

    assert result == created_user
    mock_user_repo.find_by_email.assert_called_once_with("new@example.com")
    mock_user_repo.create.assert_called_once()

@pytest.mark.asyncio
async def test_login_success_returns_token_pair(auth_service, mock_user_repo, mock_auth_repo):
    user_id = uuid.uuid4()
    user = User(id=user_id, email="user@example.com", name="User", hashed_password=hash_password("password123"))
    mock_user_repo.find_by_email = AsyncMock(return_value=user)
    mock_auth_repo.create_refresh_token = AsyncMock(
        return_value=RefreshToken(user_id=user_id, token_hash="h", expires_at=datetime.now(timezone.utc))
    )

    result = await auth_service.login(LoginRequest(email="user@example.com", password="password123"))

    assert result.access_token
    assert result.refresh_token
    assert result.token_type == "bearer"
    mock_auth_repo.create_refresh_token.assert_called_once()

@pytest.mark.asyncio
async def test_login_wrong_password_raises_unauthorized(auth_service, mock_user_repo):
    user = User(email="user@example.com", name="User", hashed_password=hash_password("correct-password"))
    mock_user_repo.find_by_email = AsyncMock(return_value=user)

    with pytest.raises(UnauthorizedException, match="Invalid credentials"):
        await auth_service.login(LoginRequest(email="user@example.com", password="wrong-password"))

@pytest.mark.asyncio
async def test_login_unknown_email_raises_unauthorized(auth_service, mock_user_repo):
    mock_user_repo.find_by_email = AsyncMock(return_value=None)

    with pytest.raises(UnauthorizedException, match="Invalid credentials"):
        await auth_service.login(LoginRequest(email="unknown@example.com", password="password123"))

@pytest.mark.asyncio
async def test_refresh_valid_token_rotates_and_returns_new_pair(auth_service, mock_auth_repo):
    user_id = uuid.uuid4()
    old_token = RefreshToken(user_id=user_id, token_hash="old-hash", expires_at=datetime.now(timezone.utc))
    mock_auth_repo.find_valid_by_hash = AsyncMock(return_value=old_token)
    mock_auth_repo.revoke = AsyncMock()
    mock_auth_repo.create_refresh_token = AsyncMock(
        return_value=RefreshToken(user_id=user_id, token_hash="new-hash", expires_at=datetime.now(timezone.utc))
    )

    result = await auth_service.refresh("some-raw-refresh-token")

    assert result.access_token
    assert result.refresh_token
    mock_auth_repo.revoke.assert_called_once_with(old_token)
    mock_auth_repo.create_refresh_token.assert_called_once()

@pytest.mark.asyncio
async def test_refresh_invalid_token_raises_unauthorized(auth_service, mock_auth_repo):
    mock_auth_repo.find_valid_by_hash = AsyncMock(return_value=None)

    with pytest.raises(UnauthorizedException, match="Invalid or expired refresh token"):
        await auth_service.refresh("bad-token")

@pytest.mark.asyncio
async def test_logout_revokes_existing_token(auth_service, mock_auth_repo):
    token_row = RefreshToken(user_id=uuid.uuid4(), token_hash="h", expires_at=datetime.now(timezone.utc))
    mock_auth_repo.find_valid_by_hash = AsyncMock(return_value=token_row)
    mock_auth_repo.revoke = AsyncMock()

    await auth_service.logout("some-token")

    mock_auth_repo.revoke.assert_called_once_with(token_row)

@pytest.mark.asyncio
async def test_logout_unknown_token_is_idempotent(auth_service, mock_auth_repo):
    mock_auth_repo.find_valid_by_hash = AsyncMock(return_value=None)
    mock_auth_repo.revoke = AsyncMock()

    await auth_service.logout("unknown-token")

    mock_auth_repo.revoke.assert_not_called()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_auth_service.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.modules.auth.service'`

- [ ] **Step 3: Implement AuthService**

Create `app/modules/auth/service.py`:

```python
from datetime import datetime, timedelta, timezone

from app.config.security import (
    create_access_token,
    generate_refresh_token,
    hash_token,
    verify_password,
)
from app.config.settings import settings
from app.core.exceptions import UnauthorizedException
from app.models.user import User
from app.modules.auth.repository import AuthRepository
from app.modules.auth.schemas import LoginRequest, TokenResponse
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import CreateUserRequest
from app.modules.users.service import UserService

class AuthService:
    def __init__(self, user_repo: UserRepository, auth_repo: AuthRepository):
        self.user_repo = user_repo
        self.auth_repo = auth_repo
        self.user_service = UserService(user_repo)

    async def register(self, request: CreateUserRequest) -> User:
        return await self.user_service.create_user(request)

    async def login(self, request: LoginRequest) -> TokenResponse:
        user = await self.user_repo.find_by_email(request.email)
        if not user or not verify_password(request.password, user.hashed_password):
            raise UnauthorizedException("Invalid credentials")
        return await self._issue_tokens(user)

    async def refresh(self, refresh_token: str) -> TokenResponse:
        token_hash = hash_token(refresh_token)
        existing = await self.auth_repo.find_valid_by_hash(token_hash)
        if not existing:
            raise UnauthorizedException("Invalid or expired refresh token")

        await self.auth_repo.revoke(existing)
        user = await self.user_repo.find_by_id(existing.user_id)
        if not user:
            raise UnauthorizedException("Invalid or expired refresh token")
        return await self._issue_tokens(user)

    async def logout(self, refresh_token: str) -> None:
        token_hash = hash_token(refresh_token)
        existing = await self.auth_repo.find_valid_by_hash(token_hash)
        if existing:
            await self.auth_repo.revoke(existing)

    async def _issue_tokens(self, user: User) -> TokenResponse:
        access_token = create_access_token(user.id)
        raw_refresh_token = generate_refresh_token()
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        await self.auth_repo.create_refresh_token(user.id, hash_token(raw_refresh_token), expires_at)

        return TokenResponse(
            access_token=access_token,
            refresh_token=raw_refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_auth_service.py -v`
Expected: PASS (8 passed)

- [ ] **Step 5: Commit**

```bash
git add app/modules/auth/service.py tests/test_auth_service.py
git commit -m "feat: implement AuthService with register/login/refresh/logout

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 6: get_current_user dependency, auth dependency providers, auth router, protected /users/me

**Files:**
- Modify: `app/core/dependencies.py`
- Create: `app/modules/auth/router.py`
- Modify: `app/modules/users/router.py`
- Modify: `app/main.py`
- Test: `tests/test_auth_router.py`

**Interfaces:**
- Consumes: `get_db` (`app.config.database`, existing), `UserRepository`/`get_user_repository` (existing, `app.core.dependencies`), `AuthRepository` (Task 3), `AuthService` (Task 5), `LoginRequest`/`RefreshRequest`/`LogoutRequest`/`TokenResponse` (Task 4), `CreateUserRequest`/`UserResponse` (`app.modules.users.schemas`, existing), `ApiResponse` (`app.core.responses`, existing), `decode_access_token` (Task 1), `UnauthorizedException` (existing).
- Produces: `get_auth_repository`, `get_auth_service`, `oauth2_scheme`, `get_current_user` in `app/core/dependencies.py`. `router` (prefix `/auth`) in `app/modules/auth/router.py`. `GET /users/me` route.

- [ ] **Step 1: Write the failing test**

Create `tests/test_auth_router.py` (uses the `client`/`db` fixtures from `tests/conftest.py`, following the vertical-flow style of `tests/test_smoke.py`):

```python
import pytest

@pytest.mark.asyncio
async def test_register_login_me_refresh_logout_flow(client):
    # Register
    register_payload = {"email": "flow@example.com", "password": "password123", "name": "Flow User"}
    register_resp = await client.post("/api/auth/register", json=register_payload)
    assert register_resp.status_code == 201
    assert register_resp.json()["data"]["email"] == "flow@example.com"

    # Login
    login_resp = await client.post("/api/auth/login", json={"email": "flow@example.com", "password": "password123"})
    assert login_resp.status_code == 200
    tokens = login_resp.json()["data"]
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]
    assert tokens["token_type"] == "bearer"

    # Access protected route
    me_resp = await client.get("/api/users/me", headers={"Authorization": f"Bearer {access_token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["data"]["email"] == "flow@example.com"

    # Protected route without token
    no_auth_resp = await client.get("/api/users/me")
    assert no_auth_resp.status_code == 401

    # Refresh
    refresh_resp = await client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_resp.status_code == 200
    new_tokens = refresh_resp.json()["data"]
    assert new_tokens["refresh_token"] != refresh_token

    # Reusing the old (rotated) refresh token must fail
    reuse_resp = await client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert reuse_resp.status_code == 401

    # Logout with the new refresh token
    logout_resp = await client.post("/api/auth/logout", json={"refresh_token": new_tokens["refresh_token"]})
    assert logout_resp.status_code == 200

    # Refresh after logout must fail
    post_logout_refresh = await client.post("/api/auth/refresh", json={"refresh_token": new_tokens["refresh_token"]})
    assert post_logout_refresh.status_code == 401

@pytest.mark.asyncio
async def test_login_wrong_password_returns_401(client):
    await client.post("/api/auth/register", json={"email": "wp@example.com", "password": "password123", "name": "WP"})
    resp = await client.post("/api/auth/login", json={"email": "wp@example.com", "password": "wrong-password"})
    assert resp.status_code == 401
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_auth_router.py -v`
Expected: FAIL with 404 on `/api/auth/register` (route doesn't exist yet)

- [ ] **Step 3: Add auth dependency providers and get_current_user**

Read `app/core/dependencies.py` first (current content shown below for reference), then replace its full content:

```python
import uuid
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.database import get_db
from app.config.security import decode_access_token
from app.core.exceptions import UnauthorizedException
from app.models.user import User
from app.modules.auth.repository import AuthRepository
from app.modules.auth.service import AuthService
from app.modules.users.repository import UserRepository
from app.modules.users.service import UserService

def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)

def get_user_service(repo: UserRepository = Depends(get_user_repository)) -> UserService:
    return UserService(repo)

def get_auth_repository(db: AsyncSession = Depends(get_db)) -> AuthRepository:
    return AuthRepository(db)

def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repository),
    auth_repo: AuthRepository = Depends(get_auth_repository),
) -> AuthService:
    return AuthService(user_repo=user_repo, auth_repo=auth_repo)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    repo: UserRepository = Depends(get_user_repository),
) -> User:
    if not token:
        raise UnauthorizedException("Not authenticated")
    payload = decode_access_token(token)
    user = await repo.find_by_id(uuid.UUID(payload["sub"]))
    if not user:
        raise UnauthorizedException("User not found")
    return user
```

- [ ] **Step 4: Implement auth router**

Create `app/modules/auth/router.py`:

```python
from fastapi import APIRouter, Depends
from app.core.dependencies import get_auth_service
from app.core.responses import ApiResponse
from app.modules.auth.schemas import LoginRequest, LogoutRequest, RefreshRequest, TokenResponse
from app.modules.auth.service import AuthService
from app.modules.users.schemas import CreateUserRequest, UserResponse

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register", response_model=ApiResponse[UserResponse], status_code=201)
async def register(
    request: CreateUserRequest,
    service: AuthService = Depends(get_auth_service),
) -> ApiResponse[UserResponse]:
    user = await service.register(request)
    return ApiResponse(data=UserResponse.model_validate(user))

@router.post("/login", response_model=ApiResponse[TokenResponse])
async def login(
    request: LoginRequest,
    service: AuthService = Depends(get_auth_service),
) -> ApiResponse[TokenResponse]:
    tokens = await service.login(request)
    return ApiResponse(data=tokens)

@router.post("/refresh", response_model=ApiResponse[TokenResponse])
async def refresh(
    request: RefreshRequest,
    service: AuthService = Depends(get_auth_service),
) -> ApiResponse[TokenResponse]:
    tokens = await service.refresh(request.refresh_token)
    return ApiResponse(data=tokens)

@router.post("/logout", response_model=ApiResponse[dict])
async def logout(
    request: LogoutRequest,
    service: AuthService = Depends(get_auth_service),
) -> ApiResponse[dict]:
    await service.logout(request.refresh_token)
    return ApiResponse(data={"message": "Logged out"})
```

- [ ] **Step 5: Add protected GET /users/me route**

Read `app/modules/users/router.py` first, then add the new route and its imports. The file's current imports are:

```python
import uuid
from fastapi import APIRouter, Depends, Query
from app.core.dependencies import get_user_service
from app.core.responses import ApiResponse, ApiListResponse
from app.core.pagination import build_pagination_info
from app.modules.users.schemas import CreateUserRequest, UserResponse
from app.modules.users.service import UserService
```

Change the import line `from app.core.dependencies import get_user_service` to:

```python
from app.core.dependencies import get_user_service, get_current_user
```

Add `from app.models.user import User` to the imports (after the `UserService` import).

Add this route to `app/modules/users/router.py`, placed immediately after the `router = APIRouter(...)` line and before `create_user`:

```python
@router.get("/me", response_model=ApiResponse[UserResponse])
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
) -> ApiResponse[UserResponse]:
    return ApiResponse(data=UserResponse.model_validate(current_user))
```

Important: this route must be registered before `@router.get("/{user_id}")` in the file — FastAPI matches routes in registration order, and `/me` would otherwise be captured by the `/{user_id}` path parameter. Verify `/me` appears above `/{user_id}` in the final file.

- [ ] **Step 6: Wire auth router into main.py**

Read `app/main.py` first, then edit. Add the import:

```python
from app.modules.auth.router import router as auth_router
```

next to the existing `from app.modules.users.router import router as users_router` line. Then add:

```python
api_router.include_router(auth_router)
```

next to the existing `api_router.include_router(users_router)` line.

- [ ] **Step 7: Run test to verify it passes**

Run: `uv run pytest tests/test_auth_router.py -v`
Expected: PASS (2 passed)

- [ ] **Step 8: Run the full test suite**

Run: `uv run pytest -v`
Expected: All tests pass (existing 35 + new tests from Tasks 1-6, no regressions in `tests/test_users_router.py` or `tests/test_smoke.py`).

- [ ] **Step 9: Commit**

```bash
git add app/core/dependencies.py app/modules/auth/router.py app/modules/users/router.py app/main.py tests/test_auth_router.py
git commit -m "feat: add auth router, get_current_user dependency, and protected /users/me route

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 7: Documentation update

**Files:**
- Modify: `README.md`
- Modify: `CLAUDE.md`

**Interfaces:**
- Consumes: nothing (documentation only).

- [ ] **Step 1: Update README.md**

Read `README.md` first. Add a new subsection under the existing features/API section documenting the auth endpoints:

```markdown
### Authentication (Phase 2)

FastIQ includes JWT-based authentication:

- `POST /api/auth/register` — create a new user (same as `POST /api/users`, exposed under `/auth` for convention).
- `POST /api/auth/login` — exchange email/password for an access token (15 min expiry) and refresh token (7 day expiry, DB-backed).
- `POST /api/auth/refresh` — exchange a valid refresh token for a new token pair. Refresh tokens rotate: each use revokes the presented token and issues a new one; reusing an old token is rejected.
- `POST /api/auth/logout` — revoke a refresh token.
- `GET /api/users/me` — example protected route; requires `Authorization: Bearer <access_token>`.

Protect any route with:

```python
from fastapi import Depends
from app.core.dependencies import get_current_user
from app.models.user import User

@router.get("/protected")
async def protected_route(current_user: User = Depends(get_current_user)):
    ...
```
```

- [ ] **Step 2: Update CLAUDE.md**

Read `CLAUDE.md` first. In the architecture/conventions section, add a line noting the `auth` module exists as the reference implementation for protected routes, alongside `users`.

- [ ] **Step 3: Run full test suite one more time**

Run: `uv run pytest -v`
Expected: All tests pass.

- [ ] **Step 4: Commit**

```bash
git add README.md CLAUDE.md
git commit -m "docs: document JWT authentication endpoints and protected route pattern

Co-Authored-By: Claude <noreply@anthropic.com>"
```
