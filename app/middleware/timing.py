import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

"""Logs and headers every response's processing time."""

logger = logging.getLogger("fleetgo.access")


class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        started = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - started) * 1000

        response.headers["X-Response-Time-ms"] = f"{elapsed_ms:.1f}"
        request_id = getattr(request.state, "request_id", "-")
        logger.info(
            "%s %s %s %.1fms request_id=%s",
            request.method, request.url.path, response.status_code,
            elapsed_ms, request_id,
        )
        return response