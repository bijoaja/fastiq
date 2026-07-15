import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.database import engine, async_session, Base, get_db

def test_database_components():
    assert engine is not None
    assert async_session is not None
    assert issubclass(Base, object)

@pytest.mark.asyncio
async def test_get_db_success():
    mock_session = AsyncMock(spec=AsyncSession)
    mock_context = AsyncMock()
    mock_context.__aenter__.return_value = mock_session

    with patch("app.config.database.async_session", return_value=mock_context):
        db_generator = get_db()
        session = await anext(db_generator)
        assert session is mock_session

        try:
            await anext(db_generator)
        except StopAsyncIteration:
            pass

        mock_session.commit.assert_awaited_once()
        mock_session.rollback.assert_not_awaited()

@pytest.mark.asyncio
async def test_get_db_exception():
    mock_session = AsyncMock(spec=AsyncSession)
    mock_context = AsyncMock()
    mock_context.__aenter__.return_value = mock_session

    with patch("app.config.database.async_session", return_value=mock_context):
        db_generator = get_db()
        session = await anext(db_generator)
        assert session is mock_session

        with pytest.raises(ValueError, match="Test error"):
            await db_generator.athrow(ValueError("Test error"))

        mock_session.rollback.assert_awaited_once()
        mock_session.commit.assert_not_awaited()
