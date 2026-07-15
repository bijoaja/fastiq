import logging
import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.config.logger import request_id_ctx
from app.utils.uuid import generate_uuid7

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging requests, injecting request_id, and timing."""
    async def dispatch(self, request: Request, call_next) -> Response:
        # Get request ID from header or generate new one
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(generate_uuid7())

        # Set to context var
        token = request_id_ctx.set(request_id)

        start_time = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception as e:
            duration = time.perf_counter() - start_time
            logger.error(
                f"Method: {request.method} | Path: {request.url.path} | "
                f"Duration: {duration:.4f}s | Status: 500 | Error: {str(e)}"
            )
            # Clean up context var even on failure
            request_id_ctx.reset(token)
            raise

        duration = time.perf_counter() - start_time

        # Inject X-Request-ID into response headers
        response.headers["X-Request-ID"] = request_id

        # Log: Method: {method} | Path: {path} | Duration: {duration:.4f}s | Status: {status_code}
        logger.info(
            f"Method: {request.method} | Path: {request.url.path} | "
            f"Duration: {duration:.4f}s | Status: {response.status_code}"
        )

        # Reset context var
        request_id_ctx.reset(token)
        return response
