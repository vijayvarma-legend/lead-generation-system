"""Request/response structured logging middleware."""

from __future__ import annotations

import time
import uuid

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        start = time.perf_counter()

        logger.info(
            "Request started",
            method=request.method,
            path=request.url.path,
            query=str(request.query_params),
            client=request.client.host if request.client else None,
        )

        response = await call_next(request)
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)

        logger.info(
            "Request finished",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            elapsed_ms=elapsed_ms,
        )

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{elapsed_ms}ms"
        return response
