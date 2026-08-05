from collections.abc import Awaitable, Callable

from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that logs request details and processing time."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        from time import perf_counter

        start_time: float = perf_counter()
        response: Response = await call_next(request)
        process_time: float = perf_counter() - start_time
        logger.info(
            f"{request.method} {request.url.path} - "
            f"{response.status_code} in {process_time:.4f}s"
        )
        return response
