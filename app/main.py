from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter
from app.config.settings import settings
from app.config.logger import setup_logging
from app.core.middleware import RequestLoggingMiddleware
from app.core.exceptions import register_exception_handlers
from app.core.responses import ApiResponse
from app.modules.users.router import router as users_router
from app.modules.auth.router import router as auth_router
# pyartisan:module_imports

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    yield

app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

# Register Middleware
app.add_middleware(RequestLoggingMiddleware)

# Register Exception Handlers
register_exception_handlers(app)

# Health Check Router
health_router = APIRouter(tags=["Health"])

@health_router.get("/health", response_model=ApiResponse[dict])
async def health_check() -> ApiResponse[dict]:
    return ApiResponse(data={"status": "ok"})

app.include_router(health_router)

# API Prefix Router for modules
api_router = APIRouter(prefix="/api")
api_router.include_router(users_router)
api_router.include_router(auth_router)
# pyartisan:modules
app.include_router(api_router)
