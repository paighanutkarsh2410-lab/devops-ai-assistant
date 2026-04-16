"""Agent health checker — monitors all dependencies and agent status.

Provides:
  - HTTP health endpoint via /health
  - Dependency checks (DB, Redis, Claude API, Prometheus)
  - Agent uptime and error tracking
  - Auto-restart on repeated failures
"""
import os
import time
import logging
import requests
import redis
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://localhost:9090")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")


class HealthChecker:
    """Checks health of all system dependencies."""

    def __init__(self):
        self.start_time = time.time()
        self.error_counts: dict[str, int] = {}
        self.last_check: Optional[datetime] = None
        self._crash_counts: dict[str, int] = {}

    def check_all(self) -> dict:
        """Run all health checks and return status."""
        checks = {
            "backend": self.check_backend(),
            "database": self.check_database(),
            "redis": self.check_redis(),
            "prometheus": self.check_prometheus(),
            "claude_api": self.check_claude_api(),
        }

        all_healthy = all(c["healthy"] for c in checks.values())
        self.last_check = datetime.now(timezone.utc)

        return {
            "status": "healthy" if all_healthy else "degraded",
            "uptime_seconds": round(time.time() - self.start_time),
            "checked_at": self.last_check.isoformat(),
            "checks": checks,
            "error_counts": dict(self.error_counts),
        }

    def check_backend(self) -> dict:
        try:
            r = requests.get(f"{BACKEND_URL}/health", timeout=5)
            return {"healthy": r.status_code == 200, "latency_ms": round(r.elapsed.total_seconds() * 1000)}
        except Exception as e:
            self._record_error("backend")
            return {"healthy": False, "error": str(e)}

    def check_database(self) -> dict:
        try:
            r = requests.get(f"{BACKEND_URL}/health", timeout=5)
            data = r.json()
            healthy = data.get("database", False)
            return {"healthy": healthy}
        except Exception as e:
            self._record_error("database")
            return {"healthy": False, "error": str(e)}

    def check_redis(self) -> dict:
        try:
            r = redis.from_url(REDIS_URL)
            r.ping()
            info = r.info("memory")
            return {
                "healthy": True,
                "used_memory_mb": round(info.get("used_memory", 0) / 1048576, 1),
            }
        except Exception as e:
            self._record_error("redis")
            return {"healthy": False, "error": str(e)}

    def check_prometheus(self) -> dict:
        try:
            r = requests.get(f"{PROMETHEUS_URL}/-/healthy", timeout=5)
            return {"healthy": r.status_code == 200}
        except Exception as e:
            self._record_error("prometheus")
            return {"healthy": False, "error": str(e)}

    def check_claude_api(self) -> dict:
        if not ANTHROPIC_API_KEY:
            return {"healthy": False, "error": "API key not configured"}
        try:
            r = requests.get(
                "https://api.anthropic.com/v1/models",
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                },
                timeout=10,
            )
            return {"healthy": r.status_code == 200}
        except Exception as e:
            self._record_error("claude_api")
            return {"healthy": False, "error": str(e)}

    def record_agent_crash(self, agent_name: str):
        """Track agent crashes for auto-restart decisions."""
        self._crash_counts[agent_name] = self._crash_counts.get(agent_name, 0) + 1
        logger.error(f"Agent {agent_name} crashed (count: {self._crash_counts[agent_name]})")

    def should_alert_humans(self, agent_name: str, threshold: int = 3) -> bool:
        """Return True if agent has crashed too many times."""
        return self._crash_counts.get(agent_name, 0) >= threshold

    def _record_error(self, component: str):
        self.error_counts[component] = self.error_counts.get(component, 0) + 1

    def get_uptime(self) -> str:
        seconds = int(time.time() - self.start_time)
        hours, remainder = divmod(seconds, 3600)
        minutes, secs = divmod(remainder, 60)
        return f"{hours}h {minutes}m {secs}s"
