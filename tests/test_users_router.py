import uuid
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from app.main import app
from app.core.dependencies import get_user_service
from app.modules.users.service import UserService
from app.models.user import User

@pytest.fixture
def mock_user_service():
    service = MagicMock(spec=UserService)
    return service

@pytest.fixture
def client(mock_user_service):
    # Override the dependency to use the mocked user service
    app.dependency_overrides[get_user_service] = lambda: mock_user_service
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["message"] == "Success"
    assert json_data["data"] == {"status": "ok"}

def test_create_user_success(client, mock_user_service):
    user_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    # Mock service.create_user to return a User model
    mock_user = User(
        id=user_id,
        email="john@example.com",
        name="John Doe",
        created_at=now,
        updated_at=now
    )
    mock_user_service.create_user = AsyncMock(return_value=mock_user)

    payload = {
        "email": "john@example.com",
        "password": "password123",
        "name": "John Doe"
    }
    response = client.post("/api/users/", json=payload)
    assert response.status_code == 201

    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"]["email"] == "john@example.com"
    assert json_data["data"]["name"] == "John Doe"
    assert "id" in json_data["data"]
    mock_user_service.create_user.assert_called_once()

def test_create_user_validation_error(client):
    payload = {
        "email": "not-an-email",
        "password": "short",
        "name": ""
    }
    response = client.post("/api/users/", json=payload)
    assert response.status_code == 422
    json_data = response.json()
    assert json_data["success"] is False
    assert "Validation Error" in json_data["message"]
    # Check that error details contain validation errors for fields
    fields = [err["field"] for err in json_data["errors"]]
    assert "body.email" in fields or "email" in fields
    assert "body.password" in fields or "password" in fields
    assert "body.name" in fields or "name" in fields

def test_get_user_success(client, mock_user_service):
    user_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    mock_user = User(
        id=user_id,
        email="john@example.com",
        name="John Doe",
        created_at=now,
        updated_at=now
    )
    mock_user_service.get_user = AsyncMock(return_value=mock_user)

    response = client.get(f"/api/users/{user_id}")
    assert response.status_code == 200

    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"]["id"] == str(user_id)
    assert json_data["data"]["email"] == "john@example.com"
    mock_user_service.get_user.assert_called_once_with(user_id)

def test_get_user_not_found(client, mock_user_service):
    from app.core.exceptions import NotFoundException
    user_id = uuid.uuid4()
    mock_user_service.get_user = AsyncMock(side_effect=NotFoundException("User not found"))

    response = client.get(f"/api/users/{user_id}")
    assert response.status_code == 404
    json_data = response.json()
    assert json_data["success"] is False
    assert json_data["message"] == "User not found"

def test_list_users_success(client, mock_user_service):
    user_id_1 = uuid.uuid4()
    user_id_2 = uuid.uuid4()
    now = datetime.now(timezone.utc)
    mock_users = [
        User(id=user_id_1, email="one@example.com", name="User One", created_at=now, updated_at=now),
        User(id=user_id_2, email="two@example.com", name="User Two", created_at=now, updated_at=now)
    ]
    mock_user_service.list_users = AsyncMock(return_value=(mock_users, 2))

    response = client.get("/api/users/?page=1&per_page=10")
    assert response.status_code == 200

    json_data = response.json()
    assert json_data["success"] is True
    assert len(json_data["data"]) == 2
    assert json_data["pagination"]["page"] == 1
    assert json_data["pagination"]["per_page"] == 10
    assert json_data["pagination"]["total"] == 2
    assert json_data["pagination"]["total_pages"] == 1
    mock_user_service.list_users.assert_called_once_with(1, 10)

def test_list_users_validation_error(client):
    # page < 1
    response = client.get("/api/users/?page=0&per_page=10")
    assert response.status_code == 422
    json_data = response.json()
    assert json_data["success"] is False

    # per_page < 1
    response = client.get("/api/users/?page=1&per_page=0")
    assert response.status_code == 422

    # per_page > 100
    response = client.get("/api/users/?page=1&per_page=101")
    assert response.status_code == 422
