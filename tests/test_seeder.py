import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.scripts.seeders.user_seeder import seed_users
from app.config.security import verify_password
from app.modules.users.repository import UserRepository

@pytest.mark.asyncio
async def test_seed_users_success(db: AsyncSession):
    # Run the seeder first time
    await seed_users(db)
    # We don't commit if the caller handles transactional state or if we just want to flush,
    # but let's commit/flush to be sure.
    await db.commit()

    # Verify the admin user exists
    repo = UserRepository(db)
    admin = await repo.find_by_email("admin@fastiq.com")
    assert admin is not None
    assert admin.name == "System Administrator"
    assert verify_password("adminpassword", admin.hashed_password)

    # Verify count is 1
    count = await repo.count_all()
    assert count == 1

    # Run seeder a second time (idempotency check)
    await seed_users(db)
    await db.commit()

    # Verify count is still 1 (no new user created)
    count2 = await repo.count_all()
    assert count2 == 1
