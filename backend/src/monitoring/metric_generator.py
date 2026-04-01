"""
Simulates service metrics for development/testing.
Generates realistic CPU, memory, error rate, and response time data
with occasional spikes for anomaly detection testing.
"""
import random
import math
import time
import threading
from .prometheus_exporter import SERVICE_CPU, SERVICE_MEMORY, SERVICE_ERROR_RATE, SERVICE_RESPONSE_TIME

SERVICES = ["web-server-01", "api-gateway", "auth-service", "database-primary", "cache-redis"]

# Baseline values for each service
BASELINES = {
    "web-server-01": {"cpu": 35, "memory": 55, "error_rate": 0.5, "response_time": 120},
    "api-gateway": {"cpu": 25, "memory": 40, "error_rate": 0.3, "response_time": 50},
    "auth-service": {"cpu": 15, "memory": 30, "error_rate": 0.1, "response_time": 80},
    "database-primary": {"cpu": 45, "memory": 65, "error_rate": 0.2, "response_time": 15},
    "cache-redis": {"cpu": 10, "memory": 50, "error_rate": 0.05, "response_time": 5},
}

_running = False
_thread = None


def _generate_value(base: float, noise: float = 5.0, spike_chance: float = 0.02) -> float:
    """Generate a realistic metric value with occasional spikes."""
    # Add time-based variation (simulates daily patterns)
    t = time.time()
    variation = math.sin(t / 300) * (base * 0.1)

    # Normal noise
    value = base + variation + random.gauss(0, noise)

    # Occasional spike
    if random.random() < spike_chance:
        spike = base * random.uniform(0.5, 1.5)
        value += spike

    return max(0, value)


def update_metrics():
    """Update all Prometheus gauge metrics with simulated values."""
    for service in SERVICES:
        baseline = BASELINES[service]
        SERVICE_CPU.labels(service=service).set(
            _generate_value(baseline["cpu"], noise=3)
        )
        SERVICE_MEMORY.labels(service=service).set(
            _generate_value(baseline["memory"], noise=2)
        )
        SERVICE_ERROR_RATE.labels(service=service).set(
            _generate_value(baseline["error_rate"], noise=0.1)
        )
        SERVICE_RESPONSE_TIME.labels(service=service).set(
            _generate_value(baseline["response_time"], noise=10)
        )


def _run_loop():
    global _running
    while _running:
        update_metrics()
        time.sleep(10)


def start_metric_generator():
    """Start background thread that generates fake metrics every 10 seconds."""
    global _running, _thread
    if _running:
        return
    _running = True
    update_metrics()  # initial values
    _thread = threading.Thread(target=_run_loop, daemon=True)
    _thread.start()
    print("Metric generator started (updating every 10s)")


def stop_metric_generator():
    global _running
    _running = False
