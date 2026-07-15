import asyncio
import logging
from app.config.logger import setup_logging
from app.config.database import async_session
from app.scripts.seeders.user_seeder import seed_users

logger = logging.getLogger(__name__)

async def main() -> None:
    setup_logging()
    logger.info("Starting database seeding...")
    async with async_session() as session:
        async with session.begin():
            await seed_users(session)
    logger.info("Database seeding completed.")

if __name__ == "__main__":
    asyncio.run(main())
