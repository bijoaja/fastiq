import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.core.exceptions import BadRequestException, NotFoundException
from app.models.user import User
from app.modules.users.schemas import CreateUserRequest
from app.modules.users.repository import UserRepository
from app.modules.users.service import UserService

@pytest.fixture
def mock_db_session():
    return AsyncMock()

@pytest.fixture
def user_repository(mock_db_session):
    return UserRepository(db=mock_db_session)

@pytest.fixture
def user_service(user_repository):
    return UserService(repo=user_repository)

@pytest.mark.asyncio
async def test_repository_create(mock_db_session, user_repository):
    user = User(email="test@example.com", name="Test User", hashed_password="hashedpassword")
    result = await user_repository.create(user)

    assert result == user
    mock_db_session.add.assert_called_once_with(user)
    mock_db_session.flush.assert_awaited_once()

@pytest.mark.asyncio
async def test_repository_find_by_id(mock_db_session, user_repository):
    user_id = uuid.uuid4()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = User(id=user_id, email="test@example.com")
    mock_db_session.execute.return_value = mock_result

    result = await user_repository.find_by_id(user_id)
    assert result is not None
    assert result.id == user_id
    mock_db_session.execute.assert_called_once()

@pytest.mark.asyncio
async def test_repository_find_by_email(mock_db_session, user_repository):
    email = "test@example.com"
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = User(email=email)
    mock_db_session.execute.return_value = mock_result

    result = await user_repository.find_by_email(email)
    assert result is not None
    assert result.email == email
    mock_db_session.execute.assert_called_once()

@pytest.mark.asyncio
async def test_repository_list_all(mock_db_session, user_repository):
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [User(email="1@example.com"), User(email="2@example.com")]
    mock_db_session.execute.return_value = mock_result

    result = await user_repository.list_all(offset=10, limit=5)
    assert len(result) == 2
    mock_db_session.execute.assert_called_once()

@pytest.mark.asyncio
async def test_repository_count_all(mock_db_session, user_repository):
    mock_result = MagicMock()
    mock_result.scalar_one.return_value = 42
    mock_db_session.execute.return_value = mock_result

    result = await user_repository.count_all()
    assert result == 42
    mock_db_session.execute.assert_called_once()

@pytest.mark.asyncio
async def test_service_create_user_success(user_service, user_repository):
    request = CreateUserRequest(email="new@example.com", name="New User", password="password123")

    # Mock find_by_email returning None (not registered yet)
    user_repository.find_by_email = AsyncMock(return_value=None)

    # Mock create returning a User
    created_user = User(email="new@example.com", name="New User", hashed_password="hashed_pass")
    user_repository.create = AsyncMock(return_value=created_user)

    result = await user_service.create_user(request)
    assert result == created_user
    user_repository.find_by_email.assert_called_once_with("new@example.com")
    user_repository.create.assert_called_once()

@pytest.mark.asyncio
async def test_service_create_user_already_registered(user_service, user_repository):
    request = CreateUserRequest(email="existing@example.com", name="New User", password="password123")

    # Mock find_by_email returning an existing user
    user_repository.find_by_email = AsyncMock(return_value=User(email="existing@example.com"))
    # Mock create to ensure we can assert it
    user_repository.create = AsyncMock()

    with pytest.raises(BadRequestException, match="Email already registered"):
        await user_service.create_user(request)

    user_repository.find_by_email.assert_called_once_with("existing@example.com")
    user_repository.create.assert_not_called()

@pytest.mark.asyncio
async def test_service_get_user_success(user_service, user_repository):
    user_id = uuid.uuid4()
    mock_user = User(id=user_id, email="test@example.com")
    user_repository.find_by_id = AsyncMock(return_value=mock_user)

    result = await user_service.get_user(user_id)
    assert result == mock_user
    user_repository.find_by_id.assert_called_once_with(user_id)

@pytest.mark.asyncio
async def test_service_get_user_not_found(user_service, user_repository):
    user_id = uuid.uuid4()
    user_repository.find_by_id = AsyncMock(return_value=None)

    with pytest.raises(NotFoundException, match="User not found"):
        await user_service.get_user(user_id)

    user_repository.find_by_id.assert_called_once_with(user_id)

@pytest.mark.asyncio
async def test_service_list_users(user_service, user_repository):
    mock_users = [User(email="1@example.com"), User(email="2@example.com")]
    user_repository.list_all = AsyncMock(return_value=mock_users)
    user_repository.count_all = AsyncMock(return_value=15)

    users, total = await user_service.list_users(page=2, per_page=5)
    assert users == mock_users
    assert total == 15
    user_repository.list_all.assert_called_once_with(offset=5, limit=5)
    user_repository.count_all.assert_called_once()
