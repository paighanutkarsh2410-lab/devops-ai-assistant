"""Metric streaming service — pushes live metrics through WebSocket."""
import asyncio
import time
import logging
import requests
import os
from datetime import datetime
from .connection_manager import manager

logger = logging.getLogger(__name__)

PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://localhost:9090")
THROTTLE_INTERVAL = 1.0  # Max 1 update per second


class MetricStreamer:
    """Streams live metrics from Prometheus to WebSocket clients."""

    def __init__(self):
        self._running = False
        self._task: asyncio.Task | None = None
        self._last_send = 0.0

    async def start(self):
        """Start streaming metrics in background."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._stream_loop())
        logger.info("MetricStreamer started")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()

    async def _stream_loop(self):
        """Periodically fetch metrics and broadcast to clients."""
        while self._running:
            try:
                if manager.connection_count > 0:
                    metrics = await self._fetch_metrics()
                    if metrics:
                        now = time.time()
                        if now - self._last_send >= THROTTLE_INTERVAL:
                            await manager.broadcast_to_all({
                                "type": "metric_update",
                                "data": metrics,
                                "timestamp": datetime.utcnow().isoformat(),
                            })
                            self._last_send = now
            except Exception as e:
                logger.debug(f"Metric stream error: {e}")

            await asyncio.sleep(5)  # Fetch every 5 seconds

    async def _fetch_metrics(self) -> dict | None:
        """Fetch current metrics from Prometheus."""
        try:
            services = {}
            # Query common metrics
            queries = {
                "cpu": 'process_cpu_seconds_total',
                "memory": 'process_resident_memory_bytes',
                "requests": 'http_requests_total',
            }

            for metric_name, query in queries.items():
                response = requests.get(
                    f"{PROMETHEUS_URL}/api/v1/query",
                    params={"query": query},
                    timeout=3,
                )
                if response.status_code == 200:
                    data = response.json()
                    for result in data.get("data", {}).get("result", []):
                        job = result.get("metric", {}).get("job", "unknown")
                        value = float(result["value"][1]) if result.get("value") else 0
                        if job not in services:
                            services[job] = {}
                        services[job][metric_name] = round(value, 2)

            return {
                "services": services,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception:
            return None

    async def stream_service(self, service_name: str) -> dict | None:
        """Fetch metrics for a specific service."""
        metrics = await self._fetch_metrics()
        if metrics and service_name in metrics.get("services", {}):
            return {
                "service": service_name,
                "metrics": metrics["services"][service_name],
                "timestamp": metrics["timestamp"],
            }
        return None


# Singleton
metric_streamer = MetricStreamer()
