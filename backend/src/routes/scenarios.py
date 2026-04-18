"""What-If Scenario Simulator: simulate infrastructure incidents and see how agents would respond."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from models import get_db
from models.user import User
from utils.auth import get_current_user
from datetime import datetime, timedelta
import random

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


class ScenarioRequest(BaseModel):
    scenario_type: str  # cpu_spike, memory_leak, disk_full, network_latency, etc.
    service: str
    severity: str = "high"
    parameters: Optional[Dict[str, Any]] = None


SCENARIO_TEMPLATES = [
    {
        "id": "cpu_spike",
        "name": "CPU Spike",
        "description": "Simulate sudden CPU usage spike on a service",
        "icon": "cpu",
        "default_params": {"cpu_percent": 95, "duration_minutes": 15, "ramp_seconds": 30},
        "affected_metrics": ["cpu_percent", "api_response_time", "error_rate"],
    },
    {
        "id": "memory_leak",
        "name": "Memory Leak",
        "description": "Simulate gradual memory consumption increase",
        "icon": "memory",
        "default_params": {"initial_percent": 60, "leak_rate_mb_per_min": 50, "oom_threshold": 95},
        "affected_metrics": ["memory_percent", "gc_pause_time", "swap_usage"],
    },
    {
        "id": "disk_full",
        "name": "Disk Full",
        "description": "Simulate disk space exhaustion from log accumulation",
        "icon": "disk",
        "default_params": {"current_percent": 75, "growth_rate_gb_per_hour": 2, "total_gb": 100},
        "affected_metrics": ["disk_percent", "iops", "write_latency"],
    },
    {
        "id": "network_latency",
        "name": "Network Latency Spike",
        "description": "Simulate increased network latency between services",
        "icon": "network",
        "default_params": {"latency_ms": 500, "packet_loss_pct": 2, "affected_routes": 3},
        "affected_metrics": ["api_response_time", "connection_timeout_rate", "request_queue_depth"],
    },
    {
        "id": "database_overload",
        "name": "Database Overload",
        "description": "Simulate database connection pool exhaustion",
        "icon": "database",
        "default_params": {"max_connections": 100, "current_connections": 98, "query_time_ms": 5000},
        "affected_metrics": ["db_connections", "query_latency", "error_rate"],
    },
    {
        "id": "cascading_failure",
        "name": "Cascading Failure",
        "description": "Simulate a failure that propagates across dependent services",
        "icon": "cascade",
        "default_params": {"origin_service": "auth-service", "propagation_delay_sec": 30, "affected_services": 4},
        "affected_metrics": ["error_rate", "api_response_time", "request_rate"],
    },
    {
        "id": "deployment_failure",
        "name": "Bad Deployment",
        "description": "Simulate a failed deployment causing error rate spike",
        "icon": "deploy",
        "default_params": {"error_rate_pct": 45, "affected_endpoints": 5, "rollback_time_sec": 120},
        "affected_metrics": ["error_rate", "http_5xx_count", "deployment_status"],
    },
    {
        "id": "ddos_attack",
        "name": "DDoS Attack",
        "description": "Simulate a distributed denial of service attack",
        "icon": "shield",
        "default_params": {"requests_per_sec": 50000, "unique_ips": 2000, "duration_minutes": 30},
        "affected_metrics": ["request_rate", "cpu_percent", "bandwidth_mbps"],
    },
]


def _simulate_agent_response(scenario: ScenarioRequest) -> Dict[str, Any]:
    """Simulate how each agent would respond to the scenario."""
    now = datetime.utcnow()
    params = scenario.parameters or {}
    svc = scenario.service

    # Monitor Agent detection
    detection_delay = random.randint(10, 60)
    monitor_response = {
        "agent": "Monitor Agent",
        "action": "Anomaly Detected",
        "timestamp": (now + timedelta(seconds=detection_delay)).isoformat(),
        "delay_seconds": detection_delay,
        "details": f"Z-score anomaly detected on {svc}: {scenario.scenario_type} exceeds threshold",
        "metrics_flagged": SCENARIO_TEMPLATES[0]["affected_metrics"]
        if not any(t["id"] == scenario.scenario_type for t in SCENARIO_TEMPLATES)
        else next((t["affected_metrics"] for t in SCENARIO_TEMPLATES if t["id"] == scenario.scenario_type), []),
    }

    # Diagnostic Agent analysis
    diag_delay = detection_delay + random.randint(5, 30)
    confidence = random.randint(72, 98)
    root_causes = {
        "cpu_spike": "Runaway process or inefficient algorithm causing CPU saturation",
        "memory_leak": "Unreleased object references in application heap causing gradual memory growth",
        "disk_full": "Unrotated log files and temporary data accumulation",
        "network_latency": "Network congestion or DNS resolution delays between service mesh nodes",
        "database_overload": "Connection pool exhaustion due to long-running queries and missing indexes",
        "cascading_failure": "Upstream service timeout causing retry storms in dependent services",
        "deployment_failure": "Breaking API change in latest deployment causing 5xx responses",
        "ddos_attack": "Volumetric DDoS attack from distributed botnet targeting public endpoints",
    }
    diagnostic_response = {
        "agent": "Diagnostic Agent",
        "action": "Root Cause Analysis",
        "timestamp": (now + timedelta(seconds=diag_delay)).isoformat(),
        "delay_seconds": diag_delay,
        "details": root_causes.get(scenario.scenario_type, "Investigating anomalous behavior pattern"),
        "confidence": confidence,
        "reasoning": [
            f"Detected {scenario.scenario_type.replace('_', ' ')} pattern on {svc}",
            f"Correlated with {random.randint(2, 5)} related metric anomalies",
            f"Historical pattern match: {random.randint(3, 12)} similar incidents in database",
            f"Severity assessment: {scenario.severity} based on blast radius analysis",
        ],
    }

    # Remediation Agent action
    rem_delay = diag_delay + random.randint(3, 15)
    remediation_actions = {
        "cpu_spike": ["Scale horizontally (add 2 instances)", "Kill runaway process PID 4521", "Enable CPU throttling"],
        "memory_leak": ["Trigger graceful restart", "Enable heap dump collection", "Scale memory limit to 4GB"],
        "disk_full": ["Rotate and compress old logs", "Clean /tmp directory", "Expand volume by 20GB"],
        "network_latency": ["Reroute traffic to secondary path", "Flush DNS cache", "Enable circuit breaker"],
        "database_overload": ["Kill long-running queries", "Increase connection pool to 200", "Enable read replica routing"],
        "cascading_failure": ["Enable circuit breakers on affected services", "Isolate failing upstream", "Activate fallback responses"],
        "deployment_failure": ["Initiate automatic rollback to v2.3.1", "Redirect traffic to canary", "Disable affected endpoints"],
        "ddos_attack": ["Enable WAF rate limiting", "Activate DDoS protection rules", "Scale edge CDN capacity"],
    }
    actions = remediation_actions.get(scenario.scenario_type, ["Investigate and apply manual fix"])
    requires_approval = scenario.severity in ("high", "critical")
    remediation_response = {
        "agent": "Remediation Agent",
        "action": "Remediation Plan",
        "timestamp": (now + timedelta(seconds=rem_delay)).isoformat(),
        "delay_seconds": rem_delay,
        "details": f"{'Awaiting approval for' if requires_approval else 'Auto-executing'}: {actions[0]}",
        "proposed_actions": actions,
        "requires_approval": requires_approval,
        "estimated_resolution_minutes": random.randint(2, 15),
        "rollback_available": True,
    }

    # Communication Agent notification
    comm_delay = diag_delay + 2
    communication_response = {
        "agent": "Communication Agent",
        "action": "Notifications Sent",
        "timestamp": (now + timedelta(seconds=comm_delay)).isoformat(),
        "delay_seconds": comm_delay,
        "details": f"Alert sent to on-call team for {scenario.severity} {scenario.scenario_type} on {svc}",
        "channels": ["Slack #incidents", "PagerDuty", "Email on-call"],
        "escalation_level": 2 if scenario.severity == "critical" else 1,
    }

    # Learning Agent observation
    learn_delay = rem_delay + random.randint(60, 300)
    learning_response = {
        "agent": "Learning Agent",
        "action": "Pattern Recorded",
        "timestamp": (now + timedelta(seconds=learn_delay)).isoformat(),
        "delay_seconds": learn_delay,
        "details": f"Incident pattern recorded for future prediction of {scenario.scenario_type} on {svc}",
        "similar_past_incidents": random.randint(1, 8),
        "model_accuracy_improvement": f"+{round(random.uniform(0.1, 2.5), 1)}%",
    }

    # Prediction Agent update
    pred_delay = learn_delay + random.randint(10, 60)
    prediction_response = {
        "agent": "Prediction Agent",
        "action": "Forecast Updated",
        "timestamp": (now + timedelta(seconds=pred_delay)).isoformat(),
        "delay_seconds": pred_delay,
        "details": f"Updated prediction model: {random.randint(70, 95)}% chance of recurrence within {random.randint(7, 30)} days",
        "next_predicted_incident": f"in {random.randint(5, 25)} days",
        "prevention_recommendations": [
            "Increase monitoring frequency for affected metrics",
            "Set up preventive scaling rules",
            "Review and optimize resource allocation",
        ],
    }

    return {
        "timeline": [
            monitor_response,
            diagnostic_response,
            communication_response,
            remediation_response,
            learning_response,
            prediction_response,
        ],
        "total_detection_time_seconds": detection_delay,
        "total_resolution_time_seconds": rem_delay + random.randint(60, 300),
        "agents_involved": 6,
        "automatic_resolution": not requires_approval,
    }


@router.get("/templates")
def get_scenario_templates(
    current_user: User = Depends(get_current_user),
):
    """Get available scenario templates."""
    return {"templates": SCENARIO_TEMPLATES}


@router.post("/simulate")
def simulate_scenario(
    scenario: ScenarioRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Run a what-if simulation and return predicted agent responses."""
    result = _simulate_agent_response(scenario)

    # Find template for extra info
    template = next((t for t in SCENARIO_TEMPLATES if t["id"] == scenario.scenario_type), None)

    return {
        "scenario": {
            "type": scenario.scenario_type,
            "service": scenario.service,
            "severity": scenario.severity,
            "parameters": scenario.parameters or (template["default_params"] if template else {}),
        },
        "simulation": result,
        "template": template,
    }
