"""Structured Logging and Observability for AutoData (P4 - Sprint 3).

Configures formatted logging, request ID tracking, and HTTP metrics middleware
while enforcing privacy rules (Art. VI: never log plain documents).
"""

from __future__ import annotations

import logging
import sys
import time
import uuid
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.config import settings

# Structured logger setup
LOG_FORMAT = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
logging.basicConfig(
    level=logging.INFO if settings.app_env != "dev" else logging.DEBUG,
    format=LOG_FORMAT,
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger("autodata.http")


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Middleware for request-id propagation, latency tracking and structured access logs."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 1. Extract or generate Request ID
        request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
        start_time = time.monotonic()

        # Attach request_id to request state for handlers
        request.state.request_id = request_id

        # 2. Process request
        try:
            response = await call_next(request)
            duration_ms = round((time.monotonic() - start_time) * 1000, 2)

            # 3. Add telemetry headers to response
            response.headers["X-Request-Id"] = request_id
            response.headers["X-Response-Time"] = f"{duration_ms}ms"

            # 4. Structured log (filtering out query params with sensitive keys)
            path = request.url.path
            logger.info(
                f"method={request.method} path={path} status={response.status_code} "
                f"duration_ms={duration_ms} req_id={request_id}"
            )
            return response
        except Exception as exc:
            duration_ms = round((time.monotonic() - start_time) * 1000, 2)
            logger.error(
                f"method={request.method} path={request.url.path} status=500 "
                f"duration_ms={duration_ms} req_id={request_id} error={exc}"
            )
            raise exc
