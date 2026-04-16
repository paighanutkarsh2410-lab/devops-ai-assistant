"""Redis caching service for production performance."""
import json
import os
import redis
from typing import Optional, Any
from functools import wraps
from datetime import datetime

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# TTL presets (seconds)
TTL_USER_SESSION = 7 * 86400      # 7 days
TTL_RECENT_METRICS = 300          # 5 minutes
TTL_FORECAST = 3600               # 1 hour
TTL_PATTERNS = 86400              # 24 hours
TTL_INCIDENTS = 60                # 1 minute
TTL_PREDICTIONS = 3600            # 1 hour
TTL_STATS = 300                   # 5 minutes


class CacheService:
    """Redis-backed caching with TTL support."""

    def __init__(self):
        try:
            self._redis = redis.from_url(REDIS_URL, decode_responses=True)
            self._redis.ping()
            self.available = True
        except Exception:
            self._redis = None
            self.available = False

    def get(self, key: str) -> Optional[Any]:
        if not self.available:
            return None
        try:
            data = self._redis.get(f"cache:{key}")
            return json.loads(data) if data else None
        except Exception:
            return None

    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        if not self.available:
            return False
        try:
            self._redis.setex(f"cache:{key}", ttl, json.dumps(value, default=str))
            return True
        except Exception:
            return False

    def delete(self, key: str) -> bool:
        if not self.available:
            return False
        try:
            self._redis.delete(f"cache:{key}")
            return True
        except Exception:
            return False

    def invalidate_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern."""
        if not self.available:
            return 0
        try:
            keys = self._redis.keys(f"cache:{pattern}")
            if keys:
                return self._redis.delete(*keys)
            return 0
        except Exception:
            return 0

    def get_stats(self) -> dict:
        if not self.available:
            return {"available": False}
        try:
            info = self._redis.info("stats")
            return {
                "available": True,
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "hit_rate": round(
                    info.get("keyspace_hits", 0) /
                    max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1) * 100, 1
                ),
                "connected_clients": self._redis.info("clients").get("connected_clients", 0),
            }
        except Exception:
            return {"available": False}


# Global instance
cache = CacheService()
