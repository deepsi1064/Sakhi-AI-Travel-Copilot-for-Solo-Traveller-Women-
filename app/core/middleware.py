"""Request-id logging, a single-process rate limiter, and API-key auth.

Both the rate limiter and auth check are intentionally minimal placeholders:
the rate limiter is in-memory (won't work correctly across multiple
instances — swap for Redis INCR/EXPIRE when that matters) and auth is a
single shared API key (swap for per-user JWTs once there are real users).
See docs/guardrails.md and docs/decisions.md.
"""
from __future__ import annotations

import time
import uuid
from collections import defaultdict, deque

import structlog
from fastapi import Header, HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings

logger = structlog.get_logger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)
        start = time.monotonic()
        response = await call_next(request)
        duration_ms = (time.monotonic() - start) * 1000
        response.headers["x-request-id"] = request_id
        logger.info(
            "request_completed",
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
        )
        return response


class InMemoryRateLimiter:
    """Sliding-window limiter per key. Single-process only."""

    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str) -> bool:
        now = time.monotonic()
        hits = self._hits[key]
        while hits and now - hits[0] > self._window_seconds:
            hits.popleft()
        if len(hits) >= self._max_requests:
            return False
        hits.append(now)
        return True


_settings = get_settings()
rate_limiter = InMemoryRateLimiter(_settings.rate_limit_requests, _settings.rate_limit_window_seconds)


def require_api_key(x_api_key: str = Header(default="")) -> None:
    settings = get_settings()
    auth_required = settings.environment == "production" or settings.api_key != "change-me"
    if auth_required and x_api_key != settings.api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid api key")


def enforce_rate_limit(request: Request) -> None:
    client_key = request.headers.get("x-api-key") or (request.client.host if request.client else "unknown")
    if not rate_limiter.check(client_key):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="rate limit exceeded")
