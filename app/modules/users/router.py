import uuid
from fastapi import APIRouter, Depends, Query
from app.core.dependencies import get_user_service, get_current_user
from app.core.responses import ApiResponse, ApiListResponse
from app.core.pagination import build_pagination_info
from app.modules.users.schemas import CreateUserRequest, UserResponse
from app.modules.users.service import UserService
from app.models.user import User

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/", response_model=ApiResponse[UserResponse], status_code=201)
async def create_user(
    request: CreateUserRequest,
    service: UserService = Depends(get_user_service)
) -> ApiResponse[UserResponse]:
    user = await service.create_user(request)
    # Convert ORM to UserResponse
    response_data = UserResponse.model_validate(user)
    return ApiResponse(data=response_data)

@router.get("/me", response_model=ApiResponse[UserResponse])
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
) -> ApiResponse[UserResponse]:
    return ApiResponse(data=UserResponse.model_validate(current_user))

@router.get("/{user_id}", response_model=ApiResponse[UserResponse])
async def get_user(
    user_id: uuid.UUID,
    service: UserService = Depends(get_user_service)
) -> ApiResponse[UserResponse]:
    user = await service.get_user(user_id)
    response_data = UserResponse.model_validate(user)
    return ApiResponse(data=response_data)

@router.get("/", response_model=ApiListResponse[UserResponse])
async def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    service: UserService = Depends(get_user_service)
) -> ApiListResponse[UserResponse]:
    users, total = await service.list_users(page, per_page)
    response_data = [UserResponse.model_validate(u) for u in users]
    pagination = build_pagination_info(page, per_page, total)
    return ApiListResponse(data=response_data, pagination=pagination)
