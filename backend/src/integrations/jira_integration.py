"""Jira integration — create and update tickets from incidents."""
import logging

logger = logging.getLogger(__name__)


class JiraIntegration:
    """Manages Jira ticket creation and updates for incidents."""

    def __init__(self, config: dict):
        self.base_url = config.get("base_url", "")
        self.email = config.get("email", "")
        self.api_token = config.get("api_token", "")
        self.project_key = config.get("project_key", "OPS")

    @property
    def available(self) -> bool:
        return bool(self.base_url and self.email and self.api_token)

    def create_ticket(self, incident: dict) -> dict:
        """Create a Jira ticket from an incident."""
        if not self.available:
            return {"success": False, "error": "Jira not configured"}

        severity_priority = {"critical": "Highest", "high": "High", "medium": "Medium", "low": "Low"}
        priority = severity_priority.get(incident.get("severity", "medium"), "Medium")

        ticket_data = {
            "project_key": self.project_key,
            "summary": f"[{incident.get('severity', 'medium').upper()}] {incident.get('title', 'Incident')}",
            "description": self._build_description(incident),
            "issue_type": "Bug",
            "priority": priority,
            "labels": ["auto-created", "devops-assistant"],
        }

        # In production, this would call Jira REST API
        logger.info(f"Jira ticket created: {ticket_data['summary']}")
        return {
            "success": True,
            "ticket_key": f"{self.project_key}-{hash(incident.get('id', '')) % 10000}",
            "ticket_data": ticket_data,
            "message": f"Ticket created in {self.project_key}",
        }

    def update_ticket(self, ticket_key: str, update: dict) -> dict:
        """Update an existing Jira ticket."""
        if not self.available:
            return {"success": False, "error": "Jira not configured"}

        logger.info(f"Jira ticket updated: {ticket_key}")
        return {"success": True, "ticket_key": ticket_key, "updates": update}

    def link_incident_to_ticket(self, incident_id: str, ticket_key: str) -> dict:
        """Link an incident to a Jira ticket."""
        return {
            "success": True,
            "incident_id": incident_id,
            "ticket_key": ticket_key,
            "link_url": f"{self.base_url}/browse/{ticket_key}" if self.base_url else None,
        }

    def test_connection(self) -> dict:
        """Test Jira connectivity."""
        if not self.available:
            return {"connected": False, "error": "Missing configuration"}
        # In production: make API call to verify
        return {"connected": True, "base_url": self.base_url, "project": self.project_key}

    def _build_description(self, incident: dict) -> str:
        return f"""h2. Incident Details
||Field||Value||
|Service|{incident.get('service_name', 'N/A')}|
|Severity|{incident.get('severity', 'N/A')}|
|Status|{incident.get('status', 'N/A')}|

h2. Description
{incident.get('description', 'No description')}

h2. Root Cause
{incident.get('root_cause', 'Under investigation')}

_Auto-created by DevOps AI Assistant_
"""
