from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from datetime import datetime, timedelta
from collections import defaultdict
import time


class RateLimitStore:
    def __init__(self):
        self._attempts: dict[str, list[float]] = defaultdict(list)
        self._window = 300  # 5 minutes
        self._max_attempts = 10  # per window

    def is_rate_limited(self, key: str) -> bool:
        now = time.time()
        cutoff = now - self._window
        self._attempts[key] = [t for t in self._attempts[key] if t > cutoff]
        return len(self._attempts[key]) >= self._max_attempts

    def record_attempt(self, key: str):
        self._attempts[key].append(time.time())

    def reset(self):
        """Drop all recorded attempts.

        The store is process-global, so tests (and any administrative reset)
        need a way to clear it without reaching into ``_attempts``.
        """
        self._attempts.clear()


rate_limit_store = RateLimitStore()


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, paths: list[str] = None):
        super().__init__(app)
        self.paths = paths or ["/api/v1/auth/login"]

    async def dispatch(self, request: Request, call_next):
        if request.method != "POST":
            return await call_next(request)

        if not any(request.url.path.startswith(p) for p in self.paths):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        key = f"auth:{client_ip}"

        if rate_limit_store.is_rate_limited(key):
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many login attempts. Please try again later."},
            )

        rate_limit_store.record_attempt(key)
        return await call_next(request)
