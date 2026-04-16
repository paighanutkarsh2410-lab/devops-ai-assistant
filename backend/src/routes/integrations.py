"""API routes for integration marketplace."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

from models import get_db
from models.user import User
from models.integration import Integration
from utils.auth import get_current_user
from integrations.jira_integration import JiraIntegration
from integrations.datadog_integration import DatadogIntegration
from integrations.github_integration import GitHubIntegration

router = APIRouter(prefix="/integrations", tags=["integrations"])


class IntegrationConnect(BaseModel):
    name: str
    config: dict = {}


AVAILABLE_INTEGRATIONS = [
    {
        "name": "jira",
        "display_name": "Jira",
        "type": "ticketing",
        "description": "Create and track tickets for incidents",
        "icon": "🎫",
        "config_fields": [
            {"key": "base_url", "label": "Jira URL", "placeholder": "https://your-domain.atlassian.net"},
            {"key": "email", "label": "Email", "placeholder": "user@company.com"},
            {"key": "api_token", "label": "API Token", "placeholder": "Your Jira API token", "secret": True},
            {"key": "project_key", "label": "Project Key", "placeholder": "OPS"},
        ],
    },
    {
        "name": "slack",
        "display_name": "Slack",
        "type": "notification",
        "description": "Send alerts and notifications to Slack channels",
        "icon": "💬",
        "config_fields": [
            {"key": "webhook_url", "label": "Webhook URL", "placeholder": "https://hooks.slack.com/...", "secret": True},
            {"key": "bot_token", "label": "Bot Token", "placeholder": "xoxb-...", "secret": True},
            {"key": "channel", "label": "Default Channel", "placeholder": "#incidents"},
        ],
    },
    {
        "name": "pagerduty",
        "display_name": "PagerDuty",
        "type": "alerting",
        "description": "Escalation and on-call management",
        "icon": "🚨",
        "config_fields": [
            {"key": "api_key", "label": "API Key", "placeholder": "Your PagerDuty API key", "secret": True},
            {"key": "service_id", "label": "Service ID", "placeholder": "P1234567"},
            {"key": "routing_key", "label": "Routing Key", "placeholder": "Events API v2 routing key", "secret": True},
        ],
    },
    {
        "name": "datadog",
        "display_name": "Datadog",
        "type": "monitoring",
        "description": "Import metrics and push events to Datadog",
        "icon": "📊",
        "config_fields": [
            {"key": "api_key", "label": "API Key", "placeholder": "Datadog API key", "secret": True},
            {"key": "app_key", "label": "Application Key", "placeholder": "Datadog app key", "secret": True},
            {"key": "site", "label": "Site", "placeholder": "datadoghq.com"},
        ],
    },
    {
        "name": "newrelic",
        "display_name": "New Relic",
        "type": "monitoring",
        "description": "APM and infrastructure monitoring",
        "icon": "🔭",
        "config_fields": [
            {"key": "api_key", "label": "API Key", "placeholder": "New Relic API key", "secret": True},
            {"key": "account_id", "label": "Account ID", "placeholder": "Your account ID"},
        ],
    },
    {
        "name": "github",
        "display_name": "GitHub",
        "type": "scm",
        "description": "Link incidents to commits and deployments",
        "icon": "🐙",
        "config_fields": [
            {"key": "token", "label": "Personal Access Token", "placeholder": "ghp_...", "secret": True},
            {"key": "owner", "label": "Owner/Org", "placeholder": "your-org"},
            {"key": "repo", "label": "Repository", "placeholder": "your-repo"},
        ],
    },
    {
        "name": "opsgenie",
        "display_name": "Opsgenie",
        "type": "alerting",
        "description": "Alert management and on-call scheduling",
        "icon": "🔔",
        "config_fields": [
            {"key": "api_key", "label": "API Key", "placeholder": "Opsgenie API key", "secret": True},
            {"key": "team", "label": "Team", "placeholder": "Your team name"},
        ],
    },
]


@router.get("/available")
def list_available():
    """List all available integrations with their config requirements."""
    return AVAILABLE_INTEGRATIONS


@router.get("/connected")
def list_connected(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List user's connected integrations."""
    integrations = db.query(Integration).filter(Integration.user_id == user.id).all()
    return [_serialize(i) for i in integrations]


@router.post("/connect", status_code=201)
def connect_integration(
    body: IntegrationConnect,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Connect a new integration."""
    avail = next((a for a in AVAILABLE_INTEGRATIONS if a["name"] == body.name), None)
    if not avail:
        raise HTTPException(400, f"Unknown integration: {body.name}")

    # Check if already connected
    existing = db.query(Integration).filter(
        Integration.user_id == user.id, Integration.name == body.name
    ).first()
    if existing:
        # Update config
        existing.config = body.config
        existing.enabled = True
        existing.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return _serialize(existing)

    integration = Integration(
        user_id=user.id,
        name=body.name,
        integration_type=avail["type"],
        config=body.config,
        enabled=True,
    )
    db.add(integration)
    db.commit()
    db.refresh(integration)
    return _serialize(integration)


@router.delete("/{integration_id}", status_code=204)
def disconnect_integration(
    integration_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    integration = db.query(Integration).filter(
        Integration.id == integration_id, Integration.user_id == user.id
    ).first()
    if not integration:
        raise HTTPException(404, "Integration not found")
    db.delete(integration)
    db.commit()


@router.post("/{integration_id}/test")
def test_integration(
    integration_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Test an integration's connectivity."""
    integration = db.query(Integration).filter(
        Integration.id == integration_id, Integration.user_id == user.id
    ).first()
    if not integration:
        raise HTTPException(404, "Integration not found")

    client = _get_client(integration)
    if client and hasattr(client, 'test_connection'):
        return client.test_connection()
    return {"connected": False, "error": "No test available for this integration"}


@router.post("/{integration_id}/toggle")
def toggle_integration(
    integration_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    integration = db.query(Integration).filter(
        Integration.id == integration_id, Integration.user_id == user.id
    ).first()
    if not integration:
        raise HTTPException(404, "Integration not found")

    integration.enabled = not integration.enabled
    integration.updated_at = datetime.utcnow()
    db.commit()
    return _serialize(integration)


def _get_client(integration: Integration):
    clients = {
        "jira": JiraIntegration,
        "datadog": DatadogIntegration,
        "github": GitHubIntegration,
    }
    cls = clients.get(integration.name)
    return cls(integration.config) if cls else None


def _serialize(i: Integration) -> dict:
    # Mask secrets in config
    safe_config = {}
    for k, v in (i.config or {}).items():
        if isinstance(v, str) and len(v) > 8:
            safe_config[k] = v[:4] + "****" + v[-4:]
        else:
            safe_config[k] = v

    return {
        "id": str(i.id),
        "name": i.name,
        "integration_type": i.integration_type,
        "config": safe_config,
        "enabled": i.enabled,
        "sync_count": i.sync_count,
        "error_count": i.error_count,
        "last_error": i.last_error,
        "last_synced": i.last_synced.isoformat() if i.last_synced else None,
        "created_at": i.created_at.isoformat() if i.created_at else None,
    }
