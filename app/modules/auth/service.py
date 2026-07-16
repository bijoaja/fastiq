from datetime import datetime, timedelta, timezone

from app.config.security import (
    create_access_token,
    generate_refresh_token,
    hash_token,
    verify_password,
)
from app.config.settings import settings
from app.core.exceptions import UnauthorizedException
from app.models.user import User
from app.modules.auth.repository import AuthRepository
from app.modules.auth.schemas import LoginRequest, TokenResponse
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import CreateUserRequest
from app.modules.users.service import UserService


class AuthService:
    def __init__(self, user_repo: UserRepository, auth_repo: AuthRepository):
        self.user_repo = user_repo
        self.auth_repo = auth_repo
        self.user_service = UserService(user_repo)

    async def register(self, request: CreateUserRequest) -> User:
        return await self.user_service.create_user(request)

    async def login(self, request: LoginRequest) -> TokenResponse:
        user = await self.user_repo.find_by_email(request.email)
        if not user or not verify_password(request.password, user.hashed_password):
            raise UnauthorizedException("Invalid credentials")
        return await self._issue_tokens(user)

    async def refresh(self, refresh_token: str) -> TokenResponse:
        token_hash = hash_token(refresh_token)
        existing = await self.auth_repo.find_valid_by_hash(token_hash)
        if not existing:
            raise UnauthorizedException("Invalid or expired refresh token")

        await self.auth_repo.revoke(existing)
        user = await self.user_repo.find_by_id(existing.user_id)
        if not user:
            raise UnauthorizedException("Invalid or expired refresh token")
        return await self._issue_tokens(user)

    async def logout(self, refresh_token: str) -> None:
        token_hash = hash_token(refresh_token)
        existing = await self.auth_repo.find_valid_by_hash(token_hash)
        if existing:
            await self.auth_repo.revoke(existing)

    async def _issue_tokens(self, user: User) -> TokenResponse:
        access_token = create_access_token(user.id)
        raw_refresh_token = generate_refresh_token()
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        await self.auth_repo.create_refresh_token(user.id, hash_token(raw_refresh_token), expires_at)

        return TokenResponse(
            access_token=access_token,
            refresh_token=raw_refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
