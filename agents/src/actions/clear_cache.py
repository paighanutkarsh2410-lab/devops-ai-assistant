"""
Clear Cache Action: Flush Redis/Memcached caches.
"""
import logging
from typing import Tuple
from .base_action import RemediationAction

logger = logging.getLogger(__name__)

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class ClearCacheAction(RemediationAction):
    name = "clear_cache"
    description = "Clear Redis cache to resolve stale data issues"
    risk_level = "LOW"
    estimated_duration_seconds = 10

    def validate(self, context: dict) -> Tuple[bool, str]:
        if not REDIS_AVAILABLE:
            return False, "Redis client not installed"
        return True, "OK"

    def execute(self, context: dict) -> dict:
        redis_url = context.get("redis_url", "redis://localhost:6379")
        pattern = context.get("cache_pattern", None)

        try:
            r = redis.from_url(redis_url, decode_responses=True)

            if pattern:
                # Delete specific keys matching pattern
                keys = list(r.scan_iter(match=pattern, count=1000))
                if keys:
                    r.delete(*keys)
                return {"success": True, "message": f"Cleared {len(keys)} keys matching '{pattern}'"}
            else:
                # Flush all (careful!)
                r.flushdb()
                return {"success": True, "message": "Cache flushed completely"}
        except Exception as e:
            return {"success": False, "message": f"Cache clear failed: {e}"}

    def rollback(self, context: dict) -> dict:
        # Cache rebuilds naturally
        return {"success": True, "message": "Cache will rebuild automatically"}
