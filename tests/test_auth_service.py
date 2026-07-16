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
async def test_refresh_valid_token_rotates_and_returns_new_pair(auth_service, mock_user_repo, mock_auth_repo):
    user_id = uuid.uuid4()
    old_token = RefreshToken(user_id=user_id, token_hash="old-hash", expires_at=datetime.now(timezone.utc))
    mock_auth_repo.find_valid_by_hash = AsyncMock(return_value=old_token)
    mock_auth_repo.revoke = AsyncMock()
    mock_auth_repo.create_refresh_token = AsyncMock(
        return_value=RefreshToken(user_id=user_id, token_hash="new-hash", expires_at=datetime.now(timezone.utc))
    )
    mock_user_repo.find_by_id = AsyncMock(
        return_value=User(id=user_id, email="user@example.com", name="User", hashed_password="hashed")
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
