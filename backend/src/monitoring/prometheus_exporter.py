from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time

# --- Metrics ---
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"]
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

ACTIVE_CONNECTIONS = Gauge(
    "active_connections",
    "Number of active connections"
)

# Service health gauges
SERVICE_CPU = Gauge("service_cpu_percent", "Service CPU usage", ["service"])
SERVICE_MEMORY = Gauge("service_memory_percent", "Service memory usage", ["service"])
SERVICE_ERROR_RATE = Gauge("service_error_rate", "Service error rate per minute", ["service"])
SERVICE_RESPONSE_TIME = Gauge("service_response_time_ms", "Service avg response time ms", ["service"])


class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        ACTIVE_CONNECTIONS.inc()
        method = request.method
        endpoint = request.url.path
        start = time.time()

        try:
            response = await call_next(request)
            status = response.status_code
        except Exception:
            status = 500
            raise
        finally:
            duration = time.time() - start
            REQUEST_COUNT.labels(method=method, endpoint=endpoint, status_code=status).inc()
            REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)
            ACTIVE_CONNECTIONS.dec()

        return response


async def metrics_endpoint(request: Request) -> Response:
    """Expose Prometheus metrics"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
