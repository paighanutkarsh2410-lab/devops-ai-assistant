"""
Example Plugin: Demonstrates how to build an AgentPlugin.

This plugin monitors HTTP endpoint response times and flags slow responses.
Use it as a template for building your own plugins.

Plugin Development Guide:
  1. Subclass AgentPlugin
  2. Implement get_metadata() with your plugin info
  3. Implement execute(context) with your logic
  4. Optionally override initialize(), cleanup(), validate_config()
  5. Place the file in agents/plugins/
  6. Enable in agents/config/plugins.yaml
"""
import time
import logging
from typing import Dict, Any, List

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from plugins.plugin_system import AgentPlugin, PluginMetadata, PluginType

logger = logging.getLogger(__name__)


class EndpointHealthPlugin(AgentPlugin):
    """
    Monitors HTTP endpoints and reports latency / availability issues.

    Config example (in plugins.yaml):
        endpoint_health:
          enabled: true
          settings:
            endpoints:
              - url: "http://api.example.com/health"
                name: "API"
                threshold_ms: 500
            check_interval_sec: 60
    """

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="Endpoint Health Monitor",
            version="1.0.0",
            author="DevOps AI Team",
            description="Monitors HTTP endpoint response times and availability",
            plugin_type=PluginType.DATA_SOURCE,
            capabilities=["http_monitoring", "latency_check", "availability_check"],
            dependencies=[],  # No extra pip packages needed
            tags=["http", "health", "latency"],
        )

    def validate_config(self) -> List[str]:
        """Validate that endpoints are configured."""
        errors = []
        endpoints = self.config.get("endpoints", [])
        if not endpoints:
            errors.append("No endpoints configured — add 'endpoints' list to settings")
        for i, ep in enumerate(endpoints):
            if "url" not in ep:
                errors.append(f"Endpoint {i} missing 'url'")
        return errors

    def initialize(self) -> bool:
        """Prepare the plugin (e.g. set up HTTP session)."""
        self._endpoints = self.config.get("endpoints", [
            {"url": "http://localhost:8000/health", "name": "Backend API", "threshold_ms": 500},
        ])
        self._results: List[Dict[str, Any]] = []
        self._initialized = True
        logger.info(f"[EndpointHealth] Initialized with {len(self._endpoints)} endpoints")
        return True

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check all configured endpoints.

        Context can include:
          - override_endpoints: list of endpoints to check instead
          - timeout: request timeout in seconds
        """
        endpoints = context.get("override_endpoints", self._endpoints)
        results = []

        for ep in endpoints:
            url = ep.get("url", "")
            name = ep.get("name", url)
            threshold = ep.get("threshold_ms", 500)

            # Simulated check (replace with real HTTP call in production)
            start = time.time()
            try:
                # In production: response = requests.get(url, timeout=context.get("timeout", 5))
                latency_ms = 45 + (hash(url) % 200)  # Simulated latency
                status_code = 200
                healthy = latency_ms < threshold
            except Exception as e:
                latency_ms = 0
                status_code = 0
                healthy = False

            results.append({
                "endpoint": name,
                "url": url,
                "status_code": status_code,
                "latency_ms": latency_ms,
                "threshold_ms": threshold,
                "healthy": healthy,
                "issue": None if healthy else f"Latency {latency_ms}ms exceeds {threshold}ms",
            })

        healthy_count = sum(1 for r in results if r["healthy"])
        return {
            "total_endpoints": len(results),
            "healthy": healthy_count,
            "unhealthy": len(results) - healthy_count,
            "results": results,
            "overall_status": "healthy" if healthy_count == len(results) else "degraded",
        }

    def cleanup(self):
        """Release resources."""
        self._results.clear()
        self._initialized = False
        logger.info("[EndpointHealth] Cleaned up")
