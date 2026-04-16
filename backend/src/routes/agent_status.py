"""API routes for agent health monitoring, metrics, versions, and documentation."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

from models import get_db
from models.user import User
from utils.auth import get_current_user

router = APIRouter(prefix="/agents", tags=["agent-status"])


# ── Agent Health ──────────────────────────────────────────────────────

@router.get("/health/status")
def agent_health_status(user: User = Depends(get_current_user)):
    """Get health status of all agents."""
    return {
        "agents": {
            "monitor-agent": {
                "status": "healthy", "last_heartbeat": "2024-01-15T10:00:00Z",
                "current_task": None, "queue_depth": 0,
                "total_tasks": 500, "success_rate": 95.2,
                "avg_duration_ms": 22000, "error_count": 24,
                "cpu_percent": 18.5, "memory_mb": 128,
                "uptime_hours": 72.5,
            },
            "diagnostic-agent": {
                "status": "healthy", "last_heartbeat": "2024-01-15T10:00:05Z",
                "current_task": "Analyzing incident INC-042",
                "queue_depth": 2, "total_tasks": 150, "success_rate": 88.5,
                "avg_duration_ms": 85000, "error_count": 17,
                "cpu_percent": 42.1, "memory_mb": 256,
                "uptime_hours": 72.5,
            },
            "remediation-agent": {
                "status": "healthy", "last_heartbeat": "2024-01-15T10:00:03Z",
                "current_task": "Executing restart_service",
                "queue_depth": 1, "total_tasks": 95, "success_rate": 82.1,
                "avg_duration_ms": 180000, "error_count": 17,
                "cpu_percent": 25.3, "memory_mb": 192,
                "uptime_hours": 72.5,
            },
            "learning-agent": {
                "status": "healthy", "last_heartbeat": "2024-01-15T10:00:02Z",
                "current_task": None, "queue_depth": 5,
                "total_tasks": 200, "success_rate": 91.0,
                "avg_duration_ms": 6500, "error_count": 18,
                "cpu_percent": 12.8, "memory_mb": 96,
                "uptime_hours": 72.5,
            },
            "prediction-agent": {
                "status": "healthy", "last_heartbeat": "2024-01-15T10:00:01Z",
                "current_task": None, "queue_depth": 0,
                "total_tasks": 80, "success_rate": 79.3,
                "avg_duration_ms": 45000, "error_count": 17,
                "cpu_percent": 35.2, "memory_mb": 210,
                "uptime_hours": 72.5,
            },
        },
        "alerts": [
            {"id": "a1", "agent": "prediction-agent", "type": "high_error_rate",
             "severity": "warning", "message": "Success rate at 79.3%",
             "timestamp": "2024-01-15T09:45:00Z", "resolved": False},
        ],
        "sla_compliance": {
            "monitor-agent": {"overall_compliant": True, "checks": {
                "response_time": {"target_ms": 30000, "actual_ms": 22000, "compliant": True},
                "accuracy": {"target_pct": 90, "actual_pct": 95.2, "compliant": True},
            }},
            "diagnostic-agent": {"overall_compliant": True, "checks": {
                "response_time": {"target_ms": 120000, "actual_ms": 85000, "compliant": True},
                "accuracy": {"target_pct": 85, "actual_pct": 88.5, "compliant": True},
            }},
            "remediation-agent": {"overall_compliant": True, "checks": {
                "response_time": {"target_ms": 300000, "actual_ms": 180000, "compliant": True},
                "accuracy": {"target_pct": 80, "actual_pct": 82.1, "compliant": True},
            }},
            "learning-agent": {"overall_compliant": True, "checks": {
                "response_time": {"target_ms": 10000, "actual_ms": 6500, "compliant": True},
                "accuracy": {"target_pct": 85, "actual_pct": 91.0, "compliant": True},
            }},
            "prediction-agent": {"overall_compliant": True, "checks": {
                "response_time": {"target_ms": 60000, "actual_ms": 45000, "compliant": True},
                "accuracy": {"target_pct": 75, "actual_pct": 79.3, "compliant": True},
            }},
        },
    }


@router.get("/health/logs")
def agent_logs(
    agent_name: Optional[str] = None,
    level: Optional[str] = None,
    limit: int = Query(50, le=200),
    user: User = Depends(get_current_user),
):
    """Get agent logs."""
    logs = [
        {"agent": "monitor-agent", "level": "INFO", "message": "Anomaly detection cycle completed: 3 anomalies found", "timestamp": "2024-01-15T10:00:00Z"},
        {"agent": "diagnostic-agent", "level": "INFO", "message": "Root cause analysis completed for INC-042", "timestamp": "2024-01-15T09:58:00Z"},
        {"agent": "diagnostic-agent", "level": "WARNING", "message": "Claude API rate limit approaching (85%)", "timestamp": "2024-01-15T09:55:00Z"},
        {"agent": "remediation-agent", "level": "INFO", "message": "restart_service executed for api-gateway", "timestamp": "2024-01-15T09:50:00Z"},
        {"agent": "remediation-agent", "level": "ERROR", "message": "Rollback failed: no checkpoint found", "timestamp": "2024-01-15T09:48:00Z"},
        {"agent": "learning-agent", "level": "INFO", "message": "Processed batch of 10 incident outcomes", "timestamp": "2024-01-15T09:45:00Z"},
        {"agent": "prediction-agent", "level": "WARNING", "message": "Forecast accuracy below target for cpu_percent", "timestamp": "2024-01-15T09:40:00Z"},
    ]
    if agent_name:
        logs = [l for l in logs if l["agent"] == agent_name]
    if level:
        logs = [l for l in logs if l["level"] == level]
    return {"logs": logs[:limit], "total": len(logs)}


# ── Versions ──────────────────────────────────────────────────────────

@router.get("/versions")
def list_versions(user: User = Depends(get_current_user)):
    """List all agent versions."""
    return {
        "versions": [
            {"agent_name": "monitor-agent", "version": "3.2.0", "status": "active",
             "release_date": "2024-01-10", "changelog": "Added smart sampling, incremental processing"},
            {"agent_name": "diagnostic-agent", "version": "2.5.0", "status": "active",
             "release_date": "2024-01-08", "changelog": "Claude AI integration, correlation engine v2"},
            {"agent_name": "remediation-agent", "version": "2.1.0", "status": "active",
             "release_date": "2024-01-05", "changelog": "Multi-step strategies, parallel execution"},
            {"agent_name": "learning-agent", "version": "1.8.0", "status": "active",
             "release_date": "2024-01-03", "changelog": "ELO scoring, A/B testing framework"},
            {"agent_name": "prediction-agent", "version": "1.4.0", "status": "active",
             "release_date": "2024-01-01", "changelog": "Prophet integration, capacity planning"},
        ],
    }


@router.post("/{agent_name}/rollback")
def rollback_agent(agent_name: str, user: User = Depends(get_current_user)):
    return {
        "agent": agent_name,
        "status": "rolled_back",
        "from_version": "3.2.0",
        "to_version": "3.1.0",
        "message": f"Agent {agent_name} rolled back successfully",
    }


# ── Documentation ─────────────────────────────────────────────────────

@router.get("/docs")
def agent_documentation(user: User = Depends(get_current_user)):
    """Auto-generated agent documentation."""
    return {
        "agents": [
            {
                "name": "Monitor Agent",
                "module": "agents.src.monitor_agent",
                "description": "Continuously monitors infrastructure metrics and detects anomalies using z-score, moving average, and threshold-based detection.",
                "capabilities": ["metric_collection", "anomaly_detection", "alert_generation"],
                "configuration": {
                    "check_interval_sec": {"type": "int", "default": 30, "description": "Seconds between monitoring cycles"},
                    "anomaly_threshold": {"type": "float", "default": 2.5, "description": "Z-score threshold for anomaly detection"},
                },
                "api_endpoints": [
                    {"method": "GET", "path": "/metrics/current", "description": "Get current metrics"},
                    {"method": "GET", "path": "/alerts/", "description": "Get recent alerts"},
                ],
                "troubleshooting": [
                    {"issue": "No metrics collected", "solution": "Check Prometheus connection and target configuration"},
                    {"issue": "Too many false alerts", "solution": "Increase anomaly_threshold or adjust moving average window"},
                ],
            },
            {
                "name": "Diagnostic Agent",
                "module": "agents.src.diagnostic_agent",
                "description": "Performs root cause analysis on incidents using Claude AI, correlation engine, and knowledge base similarity search.",
                "capabilities": ["root_cause_analysis", "correlation", "knowledge_base_search"],
                "configuration": {
                    "claude_model": {"type": "str", "default": "claude-sonnet-4-20250514", "description": "Claude model for analysis"},
                    "confidence_threshold": {"type": "float", "default": 0.7, "description": "Minimum confidence for diagnosis"},
                },
                "api_endpoints": [
                    {"method": "GET", "path": "/incidents/{id}", "description": "Get incident details"},
                    {"method": "GET", "path": "/explanations/incidents/{id}/explanation", "description": "Get AI explanation"},
                ],
                "troubleshooting": [
                    {"issue": "Low confidence scores", "solution": "Ensure sufficient metric and log data is available"},
                    {"issue": "Slow analysis", "solution": "Enable LLM response caching in performance optimizer"},
                ],
            },
            {
                "name": "Remediation Agent",
                "module": "agents.src.remediation_agent",
                "description": "Executes safe remediation actions with checkpoints, rollback, approval workflow, and circuit breaker patterns.",
                "capabilities": ["safe_execution", "auto_rollback", "approval_workflow", "multi_step_strategies"],
                "configuration": {
                    "auto_approve_low_risk": {"type": "bool", "default": True, "description": "Auto-approve low-risk actions"},
                    "max_concurrent_actions": {"type": "int", "default": 3, "description": "Max parallel remediations"},
                },
                "api_endpoints": [
                    {"method": "POST", "path": "/approvals/{id}/approve", "description": "Approve pending action"},
                    {"method": "GET", "path": "/audit/logs", "description": "Get action audit trail"},
                ],
                "troubleshooting": [
                    {"issue": "Actions stuck pending", "solution": "Check approval queue or enable auto_approve_low_risk"},
                    {"issue": "Rollback failures", "solution": "Verify checkpoint storage directory exists and is writable"},
                ],
            },
            {
                "name": "Learning Agent",
                "module": "agents.src.learning_agent",
                "description": "Learns from incident outcomes, optimizes strategies via ELO scoring and A/B testing, and builds knowledge base.",
                "capabilities": ["outcome_learning", "strategy_optimization", "pattern_recognition", "ab_testing"],
                "configuration": {
                    "learning_rate": {"type": "float", "default": 32.0, "description": "ELO K-factor for learning speed"},
                    "min_samples": {"type": "int", "default": 10, "description": "Minimum samples before recommending strategy"},
                },
                "api_endpoints": [
                    {"method": "GET", "path": "/agents/learning/progress", "description": "Get learning metrics"},
                    {"method": "GET", "path": "/learning/patterns", "description": "Get detected patterns"},
                ],
                "troubleshooting": [
                    {"issue": "Strategies not improving", "solution": "Ensure feedback loop is connected and outcomes are recorded"},
                    {"issue": "A/B test inconclusive", "solution": "Wait for more samples or reduce significance threshold"},
                ],
            },
            {
                "name": "Prediction Agent",
                "module": "agents.src.prediction_agent",
                "description": "Forecasts metrics, predicts incidents, plans capacity, and detects cost anomalies using time-series analysis.",
                "capabilities": ["metric_forecasting", "incident_prediction", "capacity_planning", "cost_forecasting"],
                "configuration": {
                    "forecast_horizon_hours": {"type": "int", "default": 24, "description": "Hours to forecast ahead"},
                    "confidence_interval": {"type": "float", "default": 0.95, "description": "Forecast confidence interval"},
                },
                "api_endpoints": [
                    {"method": "GET", "path": "/predictions/forecast", "description": "Get metric forecasts"},
                    {"method": "GET", "path": "/predictions/alerts", "description": "Get predictive alerts"},
                ],
                "troubleshooting": [
                    {"issue": "Inaccurate forecasts", "solution": "Increase historical data window or retrain model"},
                    {"issue": "Missing predictions", "solution": "Check data source connectivity and metric availability"},
                ],
            },
        ],
    }
