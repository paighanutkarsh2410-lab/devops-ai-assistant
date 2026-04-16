"""Sample test fixtures for agent testing."""

SAMPLE_INCIDENTS = [
    {
        "id": "inc-001", "title": "High CPU on api-gateway",
        "severity": "critical", "service_name": "api-gateway",
        "incident_type": "high_cpu", "status": "detected",
        "root_cause": None, "solution": None,
    },
    {
        "id": "inc-002", "title": "Memory leak in order-service",
        "severity": "high", "service_name": "order-service",
        "incident_type": "memory_leak", "status": "diagnosed",
        "root_cause": "Unbounded cache growth in OrderCache",
        "solution": "clear_cache",
    },
    {
        "id": "inc-003", "title": "API timeout on payment-service",
        "severity": "critical", "service_name": "payment-service",
        "incident_type": "api_timeout", "status": "resolved",
        "root_cause": "Database connection pool exhaustion",
        "solution": "restart_database_connection_pool",
    },
]

SAMPLE_METRICS = {
    "api-gateway": {
        "cpu_percent": 92.5, "memory_percent": 68.3,
        "request_rate": 2500, "error_rate": 4.2,
        "response_time_p95": 1850,
    },
    "order-service": {
        "cpu_percent": 45.0, "memory_percent": 89.1,
        "request_rate": 800, "error_rate": 1.5,
        "response_time_p95": 320,
    },
}

SAMPLE_STRATEGY = {
    "name": "Test Strategy",
    "mode": "sequential",
    "steps": [
        {"order": 1, "action": "run_health_check", "on_success": "step_2", "on_failure": "step_3"},
        {"order": 2, "action": "restart_service", "on_success": "complete", "on_failure": "step_3"},
        {"order": 3, "action": "escalate_to_human"},
    ],
}

SAMPLE_PLUGIN_CONFIG = {
    "endpoints": [
        {"url": "http://localhost:8000/health", "name": "Backend", "threshold_ms": 500},
    ],
}
