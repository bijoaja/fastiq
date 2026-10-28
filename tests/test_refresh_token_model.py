import uuid
from datetime import UTC, datetime

from app.models.refresh_token import RefreshToken


def test_refresh_token_model_fields():
    user_id = uuid.uuid4()
    token = RefreshToken(
        user_id=user_id,
        token_hash="a" * 64,
        expires_at=datetime.now(UTC),
    )
    assert token.user_id == user_id
    assert token.token_hash == "a" * 64
    assert token.revoked_at is None
    assert RefreshToken.__tablename__ == "refresh_tokens"
