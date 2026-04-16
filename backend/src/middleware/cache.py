"""Response caching middleware with Redis backend."""
import hashlib
import json
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from services.cache_service import cache

# TTL per endpoint pattern (path prefix → seconds)
CACHE_RULES = {
    "/metrics/": 300,          # 5 minutes
    "/metrics/aggregations": 300,
    "/predictions/": 3600,     # 1 hour
    "/predictions/metrics": 3600,
    "/predictions/capacity": 3600,
    "/predictions/costs": 3600,
    "/predictions/trends": 3600,
    "/learning/patterns": 300,
    "/learning/stats": 300,
    "/alerts/predictive/stats": 300,
    "/reports/": 600,          # 10 minutes
}


def _cache_key(request: Request) -> str | None:
    """Generate cache key for GET requests matching cache rules."""
    if request.method != "GET":
        return None
    path = request.url.path
    for prefix, _ in CACHE_RULES.items():
        if path.startswith(prefix) or path == prefix:
            raw = f"{path}?{request.url.query}"
            return f"resp:{hashlib.md5(raw.encode()).hexdigest()}"
    return None


def _get_ttl(path: str) -> int:
    """Find TTL for a given path."""
    for prefix, ttl in sorted(CACHE_RULES.items(), key=lambda x: -len(x[0])):
        if path.startswith(prefix) or path == prefix:
            return ttl
    return 60


class CacheMiddleware(BaseHTTPMiddleware):
    """Caches GET responses for configured endpoints in Redis."""

    async def dispatch(self, request: Request, call_next):
        key = _cache_key(request)

        # Try cache hit
        if key:
            cached = cache.get(key)
            if cached:
                return Response(
                    content=cached["body"],
                    status_code=cached["status"],
                    headers={**cached.get("headers", {}), "X-Cache": "HIT"},
                    media_type="application/json",
                )

        response = await call_next(request)

        # Cache successful GET responses
        if key and response.status_code == 200:
            body = b""
            async for chunk in response.body_iterator:
                body += chunk if isinstance(chunk, bytes) else chunk.encode()

            cache.set(key, {
                "body": body.decode(),
                "status": response.status_code,
                "headers": dict(response.headers),
            }, ttl=_get_ttl(request.url.path))

            return Response(
                content=body,
                status_code=response.status_code,
                headers={**dict(response.headers), "X-Cache": "MISS"},
                media_type="application/json",
            )

        return response
