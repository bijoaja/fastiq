import uuid
from datetime import datetime
import pytest
from pydantic import ValidationError
from app.config.security import hash_password, verify_password
from app.models.user import User
from app.utils.uuid import generate_uuid7
from app.modules.users.schemas import CreateUserRequest, UserResponse

def test_password_security():
    password = "secret_password"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrong_password", hashed) is False

def test_create_user_request_valid():
    data = {
        "email": "user@example.com",
        "password": "secure123",
        "name": "John Doe",
    }
    req = CreateUserRequest(**data)
    assert req.email == "user@example.com"
    assert req.password == "secure123"
    assert req.name == "John Doe"

def test_create_user_request_invalid_email():
    with pytest.raises(ValidationError):
        CreateUserRequest(
            email="invalid-email",
            password="secure123",
            name="John Doe",
        )

def test_create_user_request_invalid_password_length():
    with pytest.raises(ValidationError):
        CreateUserRequest(
            email="user@example.com",
            password="123",
            name="John Doe",
        )

def test_create_user_request_invalid_name_length():
    with pytest.raises(ValidationError):
        CreateUserRequest(
            email="user@example.com",
            password="secure123",
            name="J",
        )

def test_user_response():
    user_id = uuid.uuid4()
    now = datetime.now()
    data = {
        "id": user_id,
        "email": "user@example.com",
        "name": "John Doe",
        "created_at": now,
        "updated_at": now,
    }
    res = UserResponse(**data)
    assert res.id == user_id
    assert res.email == "user@example.com"
    assert res.name == "John Doe"
    assert res.created_at == now
    assert res.updated_at == now

def test_user_response_from_orm():
    user_id = uuid.uuid4()
    now = datetime.now()

    class MockUser:
        def __init__(self):
            self.id = user_id
            self.email = "user@example.com"
            self.name = "John Doe"
            self.created_at = now
            self.updated_at = now

    mock_user = MockUser()
    res = UserResponse.model_validate(mock_user)
    assert res.id == user_id
    assert res.email == "user@example.com"
    assert res.name == "John Doe"
    assert res.created_at == now
    assert res.updated_at == now

def test_user_model_initialization():
    user = User(
        email="user@example.com",
        hashed_password="hashed_password_string",
        name="John Doe",
    )
    assert user.email == "user@example.com"
    assert user.hashed_password == "hashed_password_string"
    assert user.name == "John Doe"
    assert User.id.default.arg.__name__ == "generate_uuid7"


