import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

RATE_LIMITED_PATHS = {
    "/api/v1/health",
    "/api/v1/health/ai-provider",
    "/api/v1/usage/events",
    "/api/v1/usage/summary",
}


@dataclass
class _Bucket:
    count: int
    reset_at: float


class PublicEndpointRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        *,
        enabled: bool,
        max_requests: int,
        window_seconds: int,
    ) -> None:
        super().__init__(app)
        self.enabled = enabled
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._buckets: dict[str, _Bucket] = {}

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if not self.enabled or request.method == "OPTIONS" or request.url.path not in RATE_LIMITED_PATHS:
            return await call_next(request)

        now = time.monotonic()
        key = f"{_client_key(request)}:{request.url.path}"
        bucket = self._buckets.get(key)
        if bucket is None or bucket.reset_at <= now:
            bucket = _Bucket(count=0, reset_at=now + self.window_seconds)
            self._buckets[key] = bucket

        retry_after = max(1, int(bucket.reset_at - now))
        if bucket.count >= self.max_requests:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again later."},
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(self.max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(retry_after),
                },
            )

        bucket.count += 1
        response = await call_next(request)
        remaining = max(0, self.max_requests - bucket.count)
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(retry_after)
        return response


def _client_key(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip() or "unknown"
    return request.client.host if request.client else "unknown"
