"""API routes for custom agent builder — CRUD, test, and templates."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from models import get_db
from models.user import User
from models.custom_agent import CustomAgent
from utils.auth import get_current_user

router = APIRouter(prefix="/agents/custom", tags=["custom-agents"])


class CustomAgentCreate(BaseModel):
    name: str
    description: str = ""
    triggers: Dict[str, Any] = {}
    data_sources: List[str] = []
    analysis_prompt: str = ""
    actions: List[Dict[str, Any]] = []
    template_id: Optional[str] = None


class CustomAgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    triggers: Optional[Dict[str, Any]] = None
    data_sources: Optional[List[str]] = None
    analysis_prompt: Optional[str] = None
    actions: Optional[List[Dict[str, Any]]] = None
    enabled: Optional[bool] = None


def _serialize(agent: CustomAgent) -> dict:
    return {
        "id": str(agent.id),
        "name": agent.name,
        "description": agent.description,
        "enabled": agent.enabled,
        "triggers": agent.triggers,
        "data_sources": agent.data_sources,
        "analysis_prompt": agent.analysis_prompt,
        "actions": agent.actions,
        "template_id": agent.template_id,
        "total_runs": agent.total_runs,
        "last_run_at": agent.last_run_at.isoformat() if agent.last_run_at else None,
        "last_result": agent.last_result,
        "created_at": agent.created_at.isoformat() if agent.created_at else None,
    }


@router.post("")
def create_custom_agent(
    body: CustomAgentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    agent = CustomAgent(
        name=body.name,
        description=body.description,
        user_id=user.id,
        triggers=body.triggers,
        data_sources=body.data_sources,
        analysis_prompt=body.analysis_prompt,
        actions=body.actions,
        template_id=body.template_id,
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return _serialize(agent)


@router.get("")
def list_custom_agents(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    agents = db.query(CustomAgent).filter(CustomAgent.user_id == user.id).all()
    return {"agents": [_serialize(a) for a in agents]}


@router.get("/templates")
def list_templates(user: User = Depends(get_current_user)):
    """Pre-built custom agent templates."""
    return {
        "templates": [
            {
                "id": "high_memory_alert",
                "name": "High Memory Alert",
                "description": "Detect when service memory usage exceeds threshold and trigger investigation",
                "triggers": {"metric": "memory_percent", "threshold": 85, "duration": "5m"},
                "data_sources": ["prometheus_metrics", "application_logs"],
                "analysis_prompt": "Analyze why memory usage for {service} exceeded {threshold}%. Check for memory leaks, unusual traffic, or recent deployments. Provide root cause and recommended action.",
                "actions": [
                    {"type": "notify_slack", "params": {"channel": "#alerts"}},
                    {"type": "check_recent_deployments", "params": {}},
                ],
            },
            {
                "id": "deployment_monitor",
                "name": "Deployment Monitor",
                "description": "Watch for new deployments and monitor health metrics post-deploy",
                "triggers": {"event": "deployment_created", "condition": "any"},
                "data_sources": ["prometheus_metrics", "application_logs", "recent_deployments"],
                "analysis_prompt": "A new deployment was made to {service}. Monitor error rates and response times for 15 minutes. Compare pre/post deployment metrics. Flag any degradation.",
                "actions": [
                    {"type": "monitor_metrics", "params": {"duration_min": 15}},
                    {"type": "notify_slack", "params": {"channel": "#deployments"}},
                ],
            },
            {
                "id": "cost_spike_detector",
                "name": "Cost Spike Detector",
                "description": "Detect unusual increases in infrastructure costs",
                "triggers": {"metric": "hourly_cost", "threshold_pct": 150, "duration": "1h"},
                "data_sources": ["cloud_billing", "prometheus_metrics"],
                "analysis_prompt": "Infrastructure costs spiked by {change_pct}% in the last hour. Identify which services/resources are driving the increase. Check for runaway scaling, idle resources, or misconfiguration.",
                "actions": [
                    {"type": "notify_slack", "params": {"channel": "#cost-alerts"}},
                    {"type": "create_ticket", "params": {"priority": "high"}},
                ],
            },
            {
                "id": "api_latency_investigator",
                "name": "API Latency Investigator",
                "description": "Investigate API endpoints with response times above threshold",
                "triggers": {"metric": "api_response_time", "threshold": 3000, "duration": "5m"},
                "data_sources": ["prometheus_metrics", "application_logs", "database_queries"],
                "analysis_prompt": "API response time for {endpoint} exceeded 3 seconds. Check database query times, external dependency latency, connection pool saturation, and recent code changes.",
                "actions": [
                    {"type": "check_database_connections", "params": {}},
                    {"type": "notify_slack", "params": {"channel": "#api-alerts"}},
                ],
            },
            {
                "id": "disk_space_watcher",
                "name": "Disk Space Watcher",
                "description": "Monitor disk usage and clean up when thresholds are reached",
                "triggers": {"metric": "disk_percent", "threshold": 80, "duration": "10m"},
                "data_sources": ["prometheus_metrics", "application_logs"],
                "analysis_prompt": "Disk usage on {host} reached {value}%. Identify largest files/directories, log rotation status, and temporary file accumulation.",
                "actions": [
                    {"type": "run_script", "params": {"script": "cleanup_logs.sh"}},
                    {"type": "notify_slack", "params": {"channel": "#infra-alerts"}},
                ],
            },
        ],
    }


@router.put("/{agent_id}")
def update_custom_agent(
    agent_id: str,
    body: CustomAgentUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    agent = db.query(CustomAgent).filter(
        CustomAgent.id == agent_id, CustomAgent.user_id == user.id
    ).first()
    if not agent:
        return {"error": "Custom agent not found"}

    for field, value in body.dict(exclude_unset=True).items():
        setattr(agent, field, value)
    db.commit()
    db.refresh(agent)
    return _serialize(agent)


@router.delete("/{agent_id}")
def delete_custom_agent(
    agent_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    agent = db.query(CustomAgent).filter(
        CustomAgent.id == agent_id, CustomAgent.user_id == user.id
    ).first()
    if not agent:
        return {"error": "Custom agent not found"}
    db.delete(agent)
    db.commit()
    return {"status": "deleted", "id": agent_id}


@router.post("/{agent_id}/test")
def test_custom_agent(
    agent_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Dry-run a custom agent and return simulated results."""
    agent = db.query(CustomAgent).filter(
        CustomAgent.id == agent_id, CustomAgent.user_id == user.id
    ).first()
    if not agent:
        return {"error": "Custom agent not found"}

    # Simulated test execution
    return {
        "agent_id": str(agent.id),
        "agent_name": agent.name,
        "status": "test_complete",
        "trigger_evaluation": {
            "would_fire": True,
            "reason": f"Metric {agent.triggers.get('metric', 'unknown')} exceeds threshold",
        },
        "data_sources_status": [
            {"source": ds, "status": "available", "sample_size": 150}
            for ds in (agent.data_sources or [])
        ],
        "analysis_preview": {
            "prompt_rendered": (agent.analysis_prompt or "")[:200] + "...",
            "estimated_tokens": len((agent.analysis_prompt or "").split()) * 2,
        },
        "actions_preview": [
            {"type": a.get("type"), "would_execute": True, "params": a.get("params", {})}
            for a in (agent.actions or [])
        ],
    }


# ── Action library ────────────────────────────────────────────────

@router.get("/actions/library")
def action_library(user: User = Depends(get_current_user)):
    """List all built-in actions available for custom agents."""
    return {
        "actions": [
            {"type": "restart_service", "label": "Restart Service", "category": "remediation",
             "params": [{"name": "service", "type": "string", "required": True}]},
            {"type": "scale_service", "label": "Scale Service", "category": "remediation",
             "params": [{"name": "replicas", "type": "number", "required": True}]},
            {"type": "run_script", "label": "Run Script", "category": "remediation",
             "params": [{"name": "script", "type": "string", "required": True}]},
            {"type": "notify_slack", "label": "Send Slack Message", "category": "notification",
             "params": [{"name": "channel", "type": "string", "required": True}]},
            {"type": "notify_email", "label": "Send Email", "category": "notification",
             "params": [{"name": "recipients", "type": "string", "required": True}]},
            {"type": "create_ticket", "label": "Create Ticket", "category": "integration",
             "params": [{"name": "priority", "type": "string", "required": False}]},
            {"type": "custom_http", "label": "Custom HTTP Request", "category": "integration",
             "params": [{"name": "url", "type": "string", "required": True},
                        {"name": "method", "type": "string", "required": False}]},
            {"type": "check_database_connections", "label": "Check DB Connections", "category": "diagnostic",
             "params": []},
            {"type": "check_recent_deployments", "label": "Check Recent Deploys", "category": "diagnostic",
             "params": []},
            {"type": "monitor_metrics", "label": "Monitor Metrics", "category": "diagnostic",
             "params": [{"name": "duration_min", "type": "number", "required": True}]},
            {"type": "rollback_deployment", "label": "Rollback Deployment", "category": "remediation",
             "params": [{"name": "deployment_id", "type": "string", "required": False}]},
            {"type": "clear_cache", "label": "Clear Cache", "category": "remediation",
             "params": [{"name": "cache_name", "type": "string", "required": False}]},
        ],
    }
