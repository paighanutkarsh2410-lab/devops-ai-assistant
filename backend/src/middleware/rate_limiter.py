"""Rate limiting middleware — per-IP with configurable tiers."""
import time
from collections import defaultdict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


# Requests per hour by tier
RATE_LIMITS = {
    "free": 100,
    "pro": 1000,
    "default": 200,  # per-IP fallback
}

# Sliding window (seconds)
WINDOW = 3600


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Token-bucket rate limiter per IP address."""

    def __init__(self, app):
        super().__init__(app)
        self._requests: dict[str, list[float]] = defaultdict(list)

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _cleanup(self, ip: str):
        cutoff = time.time() - WINDOW
        self._requests[ip] = [t for t in self._requests[ip] if t > cutoff]

    async def dispatch(self, request: Request, call_next):
        # Skip health checks and docs
        if request.url.path in ("/health", "/docs", "/openapi.json", "/metrics"):
            return await call_next(request)

        ip = self._get_client_ip(request)
        self._cleanup(ip)

        limit = RATE_LIMITS["default"]
        current = len(self._requests[ip])

        if current >= limit:
            remaining = 0
            retry_after = int(WINDOW - (time.time() - self._requests[ip][0]))
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again later."},
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "Retry-After": str(max(retry_after, 1)),
                },
            )

        self._requests[ip].append(time.time())
        remaining = limit - current - 1

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
