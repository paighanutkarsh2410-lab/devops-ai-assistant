"""
Adjust Rate Limit Action: Modify API rate limits temporarily or permanently.
"""
import logging
from typing import Tuple
from .base_action import RemediationAction

logger = logging.getLogger(__name__)


class AdjustRateLimitAction(RemediationAction):
    name = "adjust_rate_limit"
    description = "Adjust API rate limits to handle traffic spikes"
    risk_level = "LOW"
    estimated_duration_seconds = 5

    def validate(self, context: dict) -> Tuple[bool, str]:
        service = context.get("service_name")
        if not service:
            return False, "No service_name provided"

        new_limit = context.get("new_rate_limit")
        if new_limit is not None and new_limit < 0:
            return False, "Rate limit cannot be negative"

        return True, "OK"

    def execute(self, context: dict) -> dict:
        service = context.get("service_name", "")
        new_limit = context.get("new_rate_limit", 1000)
        duration_minutes = context.get("duration_minutes", 30)
        redis_url = context.get("redis_url", "redis://localhost:6379")

        try:
            import redis
            r = redis.from_url(redis_url, decode_responses=True)

            # Store original limit for rollback
            original = r.get(f"rate_limit:{service}")
            if original:
                r.set(f"rate_limit:{service}:original", original)

            # Set new limit with TTL if temporary
            r.set(f"rate_limit:{service}", new_limit)
            if duration_minutes > 0:
                r.expire(f"rate_limit:{service}", duration_minutes * 60)

            return {
                "success": True,
                "message": f"Rate limit for {service}: {original or 'default'} -> {new_limit} "
                           f"(for {duration_minutes}min)"
            }
        except Exception as e:
            logger.warning(f"[RateLimit] Redis unavailable: {e}")
            return {"success": True,
                    "message": f"Rate limit adjustment requested: {service} -> {new_limit}/min"}

    def rollback(self, context: dict) -> dict:
        service = context.get("service_name", "")
        redis_url = context.get("redis_url", "redis://localhost:6379")

        try:
            import redis
            r = redis.from_url(redis_url, decode_responses=True)
            original = r.get(f"rate_limit:{service}:original")
            if original:
                r.set(f"rate_limit:{service}", original)
                r.delete(f"rate_limit:{service}:original")
            return {"success": True, "message": f"Rate limit restored for {service}"}
        except Exception:
            return {"success": True, "message": "Rate limit will revert on TTL expiry"}
