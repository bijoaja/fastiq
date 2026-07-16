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
    bad_token = jwt.encode({"sub": "x"}, "wrong-secret-key-at-least-32-characters-long", algorithm=settings.JWT_ALGORITHM)
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
