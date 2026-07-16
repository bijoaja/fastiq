import uuid
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.database import get_db
from app.config.security import decode_access_token
from app.core.exceptions import UnauthorizedException
from app.models.user import User
from app.modules.auth.repository import AuthRepository
from app.modules.auth.service import AuthService
from app.modules.users.repository import UserRepository
from app.modules.users.service import UserService

def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)

def get_user_service(repo: UserRepository = Depends(get_user_repository)) -> UserService:
    return UserService(repo)

def get_auth_repository(db: AsyncSession = Depends(get_db)) -> AuthRepository:
    return AuthRepository(db)

def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repository),
    auth_repo: AuthRepository = Depends(get_auth_repository),
) -> AuthService:
    return AuthService(user_repo=user_repo, auth_repo=auth_repo)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    repo: UserRepository = Depends(get_user_repository),
) -> User:
    if not token:
        raise UnauthorizedException("Not authenticated")
    payload = decode_access_token(token)
    user = await repo.find_by_id(uuid.UUID(payload["sub"]))
    if not user:
        raise UnauthorizedException("User not found")
    return user
