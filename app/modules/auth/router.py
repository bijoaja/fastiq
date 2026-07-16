from fastapi import APIRouter, Depends
from app.core.dependencies import get_auth_service
from app.core.responses import ApiResponse
from app.modules.auth.schemas import LoginRequest, LogoutRequest, RefreshRequest, TokenResponse
from app.modules.auth.service import AuthService
from app.modules.users.schemas import CreateUserRequest, UserResponse

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register", response_model=ApiResponse[UserResponse], status_code=201)
async def register(
    request: CreateUserRequest,
    service: AuthService = Depends(get_auth_service),
) -> ApiResponse[UserResponse]:
    user = await service.register(request)
    return ApiResponse(data=UserResponse.model_validate(user))

@router.post("/login", response_model=ApiResponse[TokenResponse])
async def login(
    request: LoginRequest,
    service: AuthService = Depends(get_auth_service),
) -> ApiResponse[TokenResponse]:
    tokens = await service.login(request)
    return ApiResponse(data=tokens)

@router.post("/refresh", response_model=ApiResponse[TokenResponse])
async def refresh(
    request: RefreshRequest,
    service: AuthService = Depends(get_auth_service),
) -> ApiResponse[TokenResponse]:
    tokens = await service.refresh(request.refresh_token)
    return ApiResponse(data=tokens)

@router.post("/logout", response_model=ApiResponse[dict])
async def logout(
    request: LogoutRequest,
    service: AuthService = Depends(get_auth_service),
) -> ApiResponse[dict]:
    await service.logout(request.refresh_token)
    return ApiResponse(data={"message": "Logged out"})
