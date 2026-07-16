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
