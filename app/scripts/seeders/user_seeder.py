import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.modules.users.repository import UserRepository
from app.config.security import hash_password

logger = logging.getLogger(__name__)

async def seed_users(db: AsyncSession) -> None:
    repo = UserRepository(db)
    count = await repo.count_all()
    if count > 0:
        logger.info("Database already has users. Skipping user seeding.")
        return

    admin = User(
        email="admin@fastiq.com",
        hashed_password=hash_password("adminpassword"),
        name="System Administrator",
    )
    await repo.create(admin)
    logger.info("Admin user seeded successfully.")
