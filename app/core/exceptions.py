import logging
from typing import List, Optional
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError

from app.config.settings import settings
from app.core.responses import ApiErrorResponse, ErrorDetail

logger = logging.getLogger("app")

class AppException(Exception):
    def __init__(self, message: str, status_code: int = 400, errors: Optional[List[ErrorDetail]] = None):
        self.message = message
        self.status_code = status_code
        self.errors = errors or []
        super().__init__(message)

class NotFoundException(AppException):
    def __init__(self, message: str = "Not Found", errors: Optional[List[ErrorDetail]] = None):
        super().__init__(message=message, status_code=404, errors=errors)

class BadRequestException(AppException):
    def __init__(self, message: str = "Bad Request", errors: Optional[List[ErrorDetail]] = None):
        super().__init__(message=message, status_code=400, errors=errors)

class UnauthorizedException(AppException):
    def __init__(self, message: str = "Unauthorized", errors: Optional[List[ErrorDetail]] = None):
        super().__init__(message=message, status_code=401, errors=errors)

class ForbiddenException(AppException):
    def __init__(self, message: str = "Forbidden", errors: Optional[List[ErrorDetail]] = None):
        super().__init__(message=message, status_code=403, errors=errors)

class ConflictException(AppException):
    def __init__(self, message: str = "Conflict", errors: Optional[List[ErrorDetail]] = None):
        super().__init__(message=message, status_code=409, errors=errors)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    content = ApiErrorResponse(
        success=False,
        message=exc.message,
        errors=exc.errors
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=content.model_dump()
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = []
    for error in exc.errors():
        loc = error.get("loc", [])
        if len(loc) > 1:
            field = ".".join(str(x) for x in loc[1:])
        elif len(loc) == 1:
            field = str(loc[0])
        else:
            field = "unknown"

        errors.append(
            ErrorDetail(
                field=field,
                message=error.get("msg", "Validation error")
            )
        )

    content = ApiErrorResponse(
        success=False,
        message="Validation Error",
        errors=errors
    )
    return JSONResponse(
        status_code=422,
        content=content.model_dump()
    )

async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    content = ApiErrorResponse(
        success=False,
        message=exc.detail,
        errors=[]
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=content.model_dump()
    )

async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    logger.exception("Database error occurred")
    message = f"Database error: {str(exc)}" if settings.DEBUG else "Database error occurred"
    content = ApiErrorResponse(
        success=False,
        message=message,
        errors=[]
    )
    return JSONResponse(
        status_code=500,
        content=content.model_dump()
    )

async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception occurred")
    message = str(exc) if settings.DEBUG else "Internal server error"
    content = ApiErrorResponse(
        success=False,
        message=message,
        errors=[]
    )
    return JSONResponse(
        status_code=500,
        content=content.model_dump()
    )

def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    app.add_exception_handler(Exception, global_exception_handler)
