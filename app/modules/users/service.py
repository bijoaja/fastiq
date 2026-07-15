import uuid
from typing import List, Tuple
from app.core.exceptions import BadRequestException, NotFoundException
from app.config.security import hash_password
from app.models.user import User
from app.modules.users.schemas import CreateUserRequest
from app.modules.users.repository import UserRepository

class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    async def create_user(self, request: CreateUserRequest) -> User:
        existing = await self.repo.find_by_email(request.email)
        if existing:
            raise BadRequestException("Email already registered")

        hashed = hash_password(request.password)
        new_user = User(
            email=request.email,
            hashed_password=hashed,
            name=request.name
        )
        return await self.repo.create(new_user)

    async def get_user(self, user_id: uuid.UUID) -> User:
        user = await self.repo.find_by_id(user_id)
        if not user:
            raise NotFoundException("User not found")
        return user

    async def list_users(self, page: int, per_page: int) -> Tuple[List[User], int]:
        offset = (page - 1) * per_page
        users = await self.repo.list_all(offset=offset, limit=per_page)
        total = await self.repo.count_all()
        return users, total
