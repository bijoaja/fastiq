from typing import Generic, TypeVar, List, Optional
from pydantic import BaseModel, Field

T = TypeVar("T")

class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "Success"
    data: T

class PaginationInfo(BaseModel):
    page: int
    per_page: int
    total: int
    total_pages: int

class ApiListResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "Success"
    data: List[T]
    pagination: PaginationInfo

class ErrorDetail(BaseModel):
    field: Optional[str] = None
    message: str

class ApiErrorResponse(BaseModel):
    success: bool = False
    message: str
    errors: List[ErrorDetail] = Field(default_factory=list)
