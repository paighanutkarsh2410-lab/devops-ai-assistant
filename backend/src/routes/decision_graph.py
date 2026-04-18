"""Live Agent Decision Graph: shows agent nodes, event edges, and real-time decision flow."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from models import get_db
from models.user import User
from utils.auth import get_current_user
from datetime import datetime, timedelta
import random

router = APIRouter(prefix="/agents/decision-graph", tags=["decision-graph"])

# Agent definitions with their roles in the pipeline
AGENT_NODES = [
    {"id": "monitor", "label": "Monitor Agent", "group": "monitor", "size": 14,
     "description": "Collects metrics, detects anomalies via z-score analysis"},
    {"id": "diagnostic", "label": "Diagnostic Agent", "group": "diagnostic", "size": 14,
     "description": "Analyzes root cause using Claude AI, produces confidence scores"},
    {"id": "remediation", "label": "Remediation Agent", "group": "remediation", "size": 14,
     "description": "Executes safe fixes with approval workflow and rollback"},
    {"id": "learning", "label": "Learning Agent", "group": "learning", "size": 12,
     "description": "Learns from past incidents, improves future recommendations"},
    {"id": "prediction", "label": "Prediction Agent", "group": "prediction", "size": 12,
     "description": "Forecasts failures using trend analysis and pattern matching"},
    {"id": "communication", "label": "Communication Agent", "group": "communication", "size": 12,
     "description": "Sends notifications, escalates to on-call teams"},
]

# Event types that flow between agents
AGENT_EDGES = [
    {"source": "monitor", "target": "diagnostic", "label": "ANOMALY_DETECTED", "weight": 2},
    {"source": "diagnostic", "target": "remediation", "label": "DIAGNOSIS_COMPLETE", "weight": 2},
    {"source": "diagnostic", "target": "communication", "label": "ALERT_TRIGGERED", "weight": 1},
    {"source": "remediation", "target": "learning", "label": "REMEDIATION_COMPLETE", "weight": 1.5},
    {"source": "remediation", "target": "communication", "label": "APPROVAL_REQUIRED", "weight": 1},
    {"source": "learning", "target": "prediction", "label": "PATTERN_LEARNED", "weight": 1},
    {"source": "prediction", "target": "monitor", "label": "THRESHOLD_ADJUSTED", "weight": 1},
    {"source": "prediction", "target": "communication", "label": "PREDICTION_ALERT", "weight": 1},
    {"source": "learning", "target": "diagnostic", "label": "MODEL_UPDATED", "weight": 1},
]


def _generate_live_activity():
    """Generate simulated live activity for the decision graph."""
    now = datetime.utcnow()
    event_types = [
        "ANOMALY_DETECTED", "DIAGNOSIS_COMPLETE", "REMEDIATION_STARTED",
        "REMEDIATION_COMPLETE", "ALERT_TRIGGERED", "PATTERN_LEARNED",
        "PREDICTION_ALERT", "APPROVAL_REQUIRED", "THRESHOLD_ADJUSTED",
    ]
    services = ["api-server", "auth-service", "db-primary", "cache-redis", "worker-queue", "web-frontend"]
    severities = ["low", "medium", "high", "critical"]

    activities = []
    for i in range(random.randint(5, 12)):
        evt = random.choice(event_types)
        svc = random.choice(services)
        sev = random.choice(severities)
        ts = now - timedelta(minutes=random.randint(0, 120))

        # Map event to source/target agent
        edge_map = {
            "ANOMALY_DETECTED": ("monitor", "diagnostic"),
            "DIAGNOSIS_COMPLETE": ("diagnostic", "remediation"),
            "REMEDIATION_STARTED": ("remediation", "remediation"),
            "REMEDIATION_COMPLETE": ("remediation", "learning"),
            "ALERT_TRIGGERED": ("diagnostic", "communication"),
            "PATTERN_LEARNED": ("learning", "prediction"),
            "PREDICTION_ALERT": ("prediction", "communication"),
            "APPROVAL_REQUIRED": ("remediation", "communication"),
            "THRESHOLD_ADJUSTED": ("prediction", "monitor"),
        }
        src, tgt = edge_map.get(evt, ("monitor", "diagnostic"))

        activities.append({
            "event": evt,
            "source_agent": src,
            "target_agent": tgt,
            "service": svc,
            "severity": sev,
            "timestamp": ts.isoformat(),
            "message": f"{evt.replace('_', ' ').title()} for {svc}",
        })

    activities.sort(key=lambda a: a["timestamp"], reverse=True)
    return activities


def _get_agent_stats():
    """Get per-agent statistics."""
    agents = {}
    for node in AGENT_NODES:
        aid = node["id"]
        agents[aid] = {
            "events_processed": random.randint(40, 500),
            "avg_response_ms": random.randint(50, 3000),
            "success_rate": round(random.uniform(92, 99.9), 1),
            "status": random.choice(["active", "active", "active", "idle"]),
            "last_active": (datetime.utcnow() - timedelta(minutes=random.randint(0, 30))).isoformat(),
        }
    return agents


@router.get("/")
def get_decision_graph(
    current_user: User = Depends(get_current_user),
):
    """Get the full agent decision graph with nodes, edges, and live activity."""
    return {
        "nodes": AGENT_NODES,
        "edges": AGENT_EDGES,
        "activity": _generate_live_activity(),
        "agent_stats": _get_agent_stats(),
    }


@router.get("/activity")
def get_live_activity(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
):
    """Get recent agent activity/events."""
    activities = _generate_live_activity()
    return {"events": activities[:limit]}
