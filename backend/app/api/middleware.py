import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from backend.app.core.logging import logger

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for structured request logging, correlation IDs, and timing."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
        start_time = time.perf_counter()

        # Add correlation ID to request state
        request.state.request_id = request_id

        try:
            response = await call_next(request)
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{duration_ms}ms"

            # Avoid logging excessive noise for polling / health
            if not request.url.path.endswith("/health"):
                logger.info(
                    f"[{request_id}] {request.method} {request.url.path} "
                    f"-> {response.status_code} ({duration_ms}ms)"
                )

            return response
        except Exception as exc:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error(
                f"[{request_id}] {request.method} {request.url.path} "
                f"FAILED with exception: {exc} ({duration_ms}ms)"
            )
            raise
