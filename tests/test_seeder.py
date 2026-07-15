import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.models import Base
from app.scripts.seeders.user_seeder import seed_users
from app.config.security import verify_password
from app.modules.users.repository import UserRepository

# Use an in-memory SQLite database for testing
DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture
async def db_session():
    # Create engine and sessionmaker
    engine = create_async_engine(DATABASE_URL)
    async_session = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Yield session
    async with async_session() as session:
        yield session

    # Clean up / close engine
    await engine.dispose()

@pytest.mark.asyncio
async def test_seed_users_success(db_session: AsyncSession):
    # Run the seeder first time
    await seed_users(db_session)
    # We don't commit if the caller handles transactional state or if we just want to flush,
    # but let's commit/flush to be sure.
    await db_session.commit()

    # Verify the admin user exists
    repo = UserRepository(db_session)
    admin = await repo.find_by_email("admin@fastiq.com")
    assert admin is not None
    assert admin.name == "System Administrator"
    assert verify_password("adminpassword", admin.hashed_password)

    # Verify count is 1
    count = await repo.count_all()
    assert count == 1

    # Run seeder a second time (idempotency check)
    await seed_users(db_session)
    await db_session.commit()

    # Verify count is still 1 (no new user created)
    count2 = await repo.count_all()
    assert count2 == 1
