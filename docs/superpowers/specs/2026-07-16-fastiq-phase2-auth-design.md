# FastIQ Phase 2 (JWT Authentication) — Design Spec

**Date:** 2026-07-16
**Status:** Approved by user, pending self-review
**Scope:** MVP Roadmap Phase 2 (PRD.md §21), JWT authentication slice only. Pagination utilities enhancement and seeder-framework generalization are explicitly deferred to a separate iteration. Role/permission dependencies stay in Phase 3 per the original roadmap.

## Context

FastIQ Phase 1 (Foundation) is complete: FastAPI app, async SQLAlchemy, Alembic, Docker, standardized response envelope, global exception handling, structured logging, and a `users` module demonstrating router → service → repository. Password hashing (`hash_password`/`verify_password` in `app/config/security.py`) already exists but nothing issues or verifies a JWT yet — there is no login endpoint and no way to protect a route.

This spec adds the JWT authentication slice of Phase 2: register, login, refresh (DB-backed, rotating), logout, and a `get_current_user` dependency other modules can reuse to protect routes. Decisions locked in during brainstorming:

- **Token model:** short-lived JWT access token + DB-backed (stateful) refresh token, so refresh tokens can be revoked individually (logout, rotation-reuse detection) rather than only expiring client-side.
- **Refresh rotation:** every `/auth/refresh` call revokes the presented refresh token and issues a new one. Presenting an already-revoked/used token is treated as reuse and rejected — this is the standard defense against stolen refresh tokens.
- **JWT library:** PyJWT (lighter than python-jose, no JWE/JWK need here).
- **Role/permission dependencies:** out of scope — deferred to Phase 3 as originally planned.
- **Scope discipline:** this iteration is JWT auth only. Seeder framework generalization and richer pagination utilities (also nominally Phase 2 items) are separate follow-up work, not bundled here.

## Architecture

### New files

```
app/config/settings.py        # extend: JWT settings (secret reuse, algorithm, expiry minutes)
app/config/security.py        # extend: create_access_token, decode_access_token, generate_refresh_token, hash_token
app/models/refresh_token.py   # new: RefreshToken ORM model
app/models/__init__.py        # extend: register RefreshToken in Base.metadata
app/modules/auth/
├── schemas.py                # LoginRequest, TokenResponse, RefreshRequest
├── repository.py             # AuthRepository — refresh_token CRUD
├── service.py                # AuthService — register/login/refresh/logout
└── router.py                 # /api/auth/register, /login, /refresh, /logout
app/core/dependencies.py      # extend: get_current_user, oauth2_scheme
app/modules/users/router.py   # extend: GET /me (protected, demonstrates get_current_user)
tests/test_auth.py            # new: register -> login -> protected /me -> refresh -> reuse-rejected -> bad login
alembic/versions/<rev>_add_refresh_tokens.py  # new migration for refresh_tokens table
```

### Token design

- **Access token:** JWT, `sub` = user id (str), `exp` = now + `ACCESS_TOKEN_EXPIRE_MINUTES` (default 15), signed HS256 with `settings.SECRET_KEY`. Stateless — no DB row. Verified by decoding + checking `exp`/signature only.
- **Refresh token:** opaque random string (`secrets.token_urlsafe(32)`) returned to the client as-is; only its SHA-256 hash is stored in `refresh_tokens` (never the raw value) — same principle as password hashing, avoids a DB leak handing out valid tokens directly. Row carries `user_id`, `token_hash`, `expires_at`, `revoked_at` (nullable), `created_at`.
- **Rotation:** `POST /auth/refresh` looks up the presented token's hash. If missing, already revoked, or expired → `UnauthorizedException`. Otherwise: mark it revoked, issue a new access + refresh pair, store the new refresh token's hash, return both.

### `RefreshToken` model (`app/models/refresh_token.py`)

Centralized like `User`, per FastIQ's models convention.

```python
id: Mapped[uuid.UUID]          # primary key, generate_uuid7
user_id: Mapped[uuid.UUID]     # FK -> users.id
token_hash: Mapped[str]        # String(64), unique, index — sha256 hex digest
expires_at: Mapped[datetime]   # DateTime(timezone=True)
revoked_at: Mapped[Optional[datetime]]  # DateTime(timezone=True), nullable
created_at: Mapped[datetime]   # default func.now()
```

### `app/config/security.py` additions

- `create_access_token(user_id: uuid.UUID) -> str` — encodes `{"sub": str(user_id), "exp": ...}` with PyJWT.
- `decode_access_token(token: str) -> dict` — decodes and verifies; raises `UnauthorizedException("Invalid or expired token")` on any `jwt.PyJWTError`.
- `generate_refresh_token() -> str` — `secrets.token_urlsafe(32)`.
- `hash_token(token: str) -> str` — `hashlib.sha256(token.encode()).hexdigest()`.

### `app/config/settings.py` additions

- `ACCESS_TOKEN_EXPIRE_MINUTES: int = 15`
- `REFRESH_TOKEN_EXPIRE_DAYS: int = 7`
- `JWT_ALGORITHM: str = "HS256"`
- (Reuses existing `SECRET_KEY` — no new secret needed.)

### Auth module

- **`repository.py` (`AuthRepository`):** `create_refresh_token(user_id, token_hash, expires_at) -> RefreshToken`, `find_valid_by_hash(token_hash) -> Optional[RefreshToken]` (query filters `revoked_at IS NULL AND expires_at > now()`), `revoke(refresh_token: RefreshToken) -> None` (sets `revoked_at = func.now()`).
- **`service.py` (`AuthService`, depends on `UserRepository` + `AuthRepository`):**
  - `register(request: CreateUserRequest) -> User` — thin delegation to a `UserService` instance (reuses existing `create_user`, including its duplicate-email check — no logic duplicated).
  - `login(request: LoginRequest) -> TokenResponse` — `find_by_email`; if missing or `verify_password` fails, raise `UnauthorizedException("Invalid credentials")` (same message either way — don't leak which field was wrong); otherwise issue token pair via a shared `_issue_tokens(user)` helper.
  - `refresh(refresh_token: str) -> TokenResponse` — hash input, `find_valid_by_hash`; if `None`, raise `UnauthorizedException("Invalid or expired refresh token")`; else revoke it and call `_issue_tokens(user)`.
  - `logout(refresh_token: str) -> None` — hash input, look up, revoke if found (idempotent — no error if already gone/expired, logout should never fail loudly).
  - `_issue_tokens(user) -> TokenResponse` — creates access token, generates+hashes+stores new refresh token, returns `TokenResponse(access_token, refresh_token, token_type="bearer", expires_in=<access ttl seconds>)`.
- **`router.py`** (prefix `/auth`, tag `Auth`):
  - `POST /register` → 201, `ApiResponse[UserResponse]`
  - `POST /login` → 200, `ApiResponse[TokenResponse]`
  - `POST /refresh` → 200, `ApiResponse[TokenResponse]`
  - `POST /logout` → 200, `ApiResponse[dict]` (`{"message": "Logged out"}`)
  - All business logic stays in `AuthService` — router only validates input and calls service, same pattern as `users/router.py`.

### `get_current_user` dependency (`app/core/dependencies.py`)

```python
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    repo: UserRepository = Depends(get_user_repository),
) -> User:
    payload = decode_access_token(token)
    user = await repo.find_by_id(uuid.UUID(payload["sub"]))
    if not user:
        raise UnauthorizedException("User not found")
    return user
```

`app/modules/users/router.py` gets one new route, `GET /me`, using `Depends(get_current_user)` — this is the template's demonstration of how any future module protects a route.

### Migration

New Alembic revision (autogenerated against the new `RefreshToken` model) adds the `refresh_tokens` table with a foreign key to `users.id`.

### Error handling

No new exception types — reuses `UnauthorizedException` (401) and `BadRequestException` (400, via the existing duplicate-email path in `create_user`) already defined in `app/core/exceptions.py`. No per-endpoint try/except, consistent with the rest of the codebase.

## Testing

`tests/test_auth.py`, built on the existing `client`/`db` fixtures in `tests/conftest.py`:
1. Register → 201, user created.
2. Login with correct credentials → 200, access + refresh token returned.
3. Login with wrong password → 401.
4. `GET /api/users/me` with the access token → 200, returns the registered user.
5. `GET /api/users/me` with no/garbage token → 401.
6. Refresh with the valid refresh token → 200, new token pair returned.
7. Re-using the now-rotated (old) refresh token → 401 (proves rotation/reuse rejection).
8. Logout, then attempt refresh with the logged-out token → 401.

## Out of scope for this iteration (explicit deferrals)

- Role/permission dependencies (`require_role`, permission checks) — Phase 3, PRD §14.
- Seeder framework generalization (multi-seeder orchestrator) — separate iteration.
- Pagination utilities beyond the existing minimal helper — separate iteration.
- Rate limiting on login/refresh endpoints (PRD §14 lists this as optional) — not included.
- Logout-all-devices / revoke-all-for-user bulk operation — single-token logout only for now.
