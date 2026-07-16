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
