import time
import uuid

import jwt
import pytest

from app.config.security import (
    create_access_token,
    decode_access_token,
    generate_refresh_token,
    hash_token,
)
from app.config.settings import settings
from app.core.exceptions import UnauthorizedException


def test_create_and_decode_access_token():
    user_id = uuid.uuid4()
    token = create_access_token(user_id)
    payload = decode_access_token(token)
    assert payload["sub"] == str(user_id)


def test_decode_access_token_invalid_signature_raises():
    bad_token = jwt.encode(
        {"sub": "x"},
        "wrong-secret-key-at-least-32-characters-long",
        algorithm=settings.JWT_ALGORITHM,
    )
    with pytest.raises(UnauthorizedException):
        decode_access_token(bad_token)


def test_decode_access_token_expired_raises():
    expired_payload = {"sub": "x", "exp": int(time.time()) - 10}
    expired_token = jwt.encode(
        expired_payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
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


def test_get_current_user_malformed_sub_returns_401():
    from fastapi.testclient import TestClient

    from app.main import app

    token = jwt.encode(
        {"sub": "not-a-uuid", "exp": int(time.time()) + 60},
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    with TestClient(app) as client:
        response = client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_settings_rejects_short_secret_key():
    from pydantic import ValidationError

    from app.config.settings import Settings

    with pytest.raises(ValidationError):
        Settings(DATABASE_URL="sqlite+aiosqlite:///:memory:", SECRET_KEY="short")
