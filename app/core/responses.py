from typing import TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiResponse[T](BaseModel):
    success: bool = True
    message: str = "Success"
    data: T


class PaginationInfo(BaseModel):
    page: int
    per_page: int
    total: int
    total_pages: int


class ApiListResponse[T](BaseModel):
    success: bool = True
    message: str = "Success"
    data: list[T]
    pagination: PaginationInfo


class ErrorDetail(BaseModel):
    field: str | None = None
    message: str


class ApiErrorResponse(BaseModel):
    success: bool = False
    message: str
    errors: list[ErrorDetail] = Field(default_factory=list)
