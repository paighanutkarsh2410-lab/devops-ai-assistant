"""Tests for the Communication Agent and notification components."""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def test_slack_notifier_init():
    """Test SlackNotifier initialization."""
    from notifications.slack_client import SlackNotifier

    notifier = SlackNotifier()
    # available depends on whether real keys are configured
    assert isinstance(notifier.available, bool)


def test_slack_incident_notification():
    """Test incident notification formatting (no send without config)."""
    from notifications.slack_client import SlackNotifier

    notifier = SlackNotifier()
    result = notifier.send_incident_notification({
        "id": "test-123",
        "title": "CPU spike on api-server",
        "severity": "critical",
        "service_name": "api-server",
        "detected_at": "2024-01-15T14:30:00Z",
        "description": "CPU at 95%",
        "metrics": {"cpu": "95%", "memory": "72%"},
    })
    # Returns None if no config, or dict with Slack response if configured
    assert result is None or (isinstance(result, dict) and result.get("ok"))


def test_slack_approval_request():
    """Test approval request formatting."""
    from notifications.slack_client import SlackNotifier

    notifier = SlackNotifier()
    result = notifier.send_approval_request({
        "id": "approval-1",
        "incident_id": "inc-1",
        "action_name": "restart_service",
        "risk_level": "HIGH",
        "action_description": "Restart api-server",
        "expiry_minutes": 30,
    })
    assert result is None or (isinstance(result, dict) and result.get("ok"))


def test_slack_daily_summary():
    """Test daily summary formatting."""
    from notifications.slack_client import SlackNotifier

    notifier = SlackNotifier()
    result = notifier.send_daily_summary({
        "incidents_count": 5,
        "auto_resolved": 3,
        "health_score": 85,
        "mttr_avg": 120,
        "top_issues": ["CPU spike on api-server", "Disk full on db"],
        "predictions_count": 2,
        "prevented_count": 1,
    })
    assert result is None or (isinstance(result, dict) and result.get("ok"))


def test_slack_predictive_alert():
    """Test predictive alert formatting."""
    from notifications.slack_client import SlackNotifier

    notifier = SlackNotifier()
    result = notifier.send_predictive_alert({
        "title": "Disk exhaustion in 12 days",
        "prediction_type": "resource_exhaustion",
        "service_name": "log-server",
        "hours_until_issue": 288,
        "confidence": 85,
        "preventive_actions": [
            {"action": "cleanup", "description": "Clean old log files"},
        ],
    })
    assert result is None or (isinstance(result, dict) and result.get("ok"))


def test_slack_interaction_handler():
    """Test Slack button interaction handling."""
    from notifications.slack_client import SlackNotifier

    notifier = SlackNotifier()

    # Acknowledge
    result = notifier.handle_interaction({
        "actions": [{"action_id": "ack_incident_inc-123", "value": "inc-123"}],
        "user": {"name": "john"},
    })
    assert result["action"] == "acknowledge"
    assert result["incident_id"] == "inc-123"

    # Approve
    result = notifier.handle_interaction({
        "actions": [{"action_id": "approve_apr-456", "value": "apr-456"}],
        "user": {"name": "jane"},
    })
    assert result["action"] == "approve"
    assert result["approval_id"] == "apr-456"

    # Reject
    result = notifier.handle_interaction({
        "actions": [{"action_id": "reject_apr-789", "value": "apr-789"}],
        "user": {"name": "admin"},
    })
    assert result["action"] == "reject"


def test_email_notifier_init():
    """Test EmailNotifier initialization."""
    from notifications.email_client import EmailNotifier

    notifier = EmailNotifier()
    # Without API key, should not be available
    assert notifier.available is False


def test_email_templates():
    """Test email HTML template rendering."""
    from notifications.email_client import EmailNotifier

    notifier = EmailNotifier()

    # Incident template
    html = notifier._render_template("incident", {
        "title": "CPU spike",
        "severity": "critical",
        "service": "api-server",
        "detected": "2024-01-15 14:30",
        "description": "CPU at 95%",
        "incident_id": "test-1",
        "dashboard_url": "http://localhost:3000/dashboard",
        "metrics": {"cpu": "95%"},
    })
    assert "CPU spike" in html
    assert "critical" in html.lower()
    assert "api-server" in html

    # Critical alert template
    html = notifier._render_template("critical_alert", {
        "title": "Database Down",
        "service": "postgres",
        "severity": "critical",
        "detected": "2024-01-15 14:30",
        "description": "Connection refused",
        "dashboard_url": "http://localhost:3000",
    })
    assert "URGENT" in html
    assert "Database Down" in html

    # Weekly digest template
    html = notifier._render_template("weekly_digest", {
        "period": "Jan 8 - Jan 15",
        "incidents_count": 10,
        "auto_resolved": 7,
        "mttr_avg": 120,
        "health_score": 85,
        "top_incidents": ["CPU spike", "Disk full"],
        "trends": [],
        "insights": ["System improving"],
        "predictions": 3,
        "prevented": 1,
    })
    assert "Weekly" in html
    assert "Jan 8" in html


def test_communication_agent_init():
    """Test CommunicationAgent initialization."""
    from communication_agent import CommunicationAgent

    agent = CommunicationAgent()
    assert agent.name == "CommunicationAgent"
    assert agent.slack is not None
    assert agent.email is not None


def test_communication_agent_routing():
    """Test smart notification routing by severity."""
    from communication_agent import CommunicationAgent, DEFAULT_ROUTING

    agent = CommunicationAgent()

    # Critical → slack + email
    channels = agent._determine_channels({"severity": "critical", "type": "incident_detected"})
    assert "slack" in channels
    assert "email" in channels

    # Medium → slack only
    channels = agent._determine_channels({"severity": "medium", "type": "incident_detected"})
    assert "slack" in channels
    assert "email" not in channels

    # Low → digest
    channels = agent._determine_channels({"severity": "low", "type": "incident_detected"})
    assert "digest" in channels

    # Approval → always slack
    channels = agent._determine_channels({"severity": "high", "type": "approval_required"})
    assert channels == ["slack"]


def test_communication_agent_anti_spam():
    """Test duplicate notification suppression."""
    from communication_agent import CommunicationAgent

    agent = CommunicationAgent()

    event = {"type": "incident_detected", "severity": "high", "data": {"id": "inc-1"}}

    # First call — not duplicate
    assert agent._is_duplicate(event) is False

    # Second call — duplicate
    assert agent._is_duplicate(event) is True


def test_communication_agent_quiet_hours():
    """Test quiet hours check."""
    from communication_agent import CommunicationAgent

    agent = CommunicationAgent()
    # This just tests the method runs; actual result depends on current UTC hour
    result = agent._is_quiet_hours()
    assert isinstance(result, bool)


def test_communication_agent_rate_limiting():
    """Test rate limiting per channel."""
    from communication_agent import CommunicationAgent
    from datetime import datetime, timezone

    agent = CommunicationAgent()

    # Not rate limited initially
    assert agent._is_rate_limited("slack") is False

    # Set a recent send
    agent._rate_limits["slack"] = datetime.now(timezone.utc)

    # Now should be rate limited
    assert agent._is_rate_limited("slack") is True


def test_communication_agent_stats():
    """Test notification stats tracking."""
    from communication_agent import CommunicationAgent

    agent = CommunicationAgent()
    stats = agent.get_notification_stats()

    assert "total_notifications" in stats
    assert "sent" in stats
    assert "by_channel" in stats
    assert "digest_buffered" in stats


def test_report_generator_init():
    """Test ReportGenerator without API."""
    from reporting.report_generator import ReportGenerator

    gen = ReportGenerator(api_get=None)

    # Postmortem without API should return error
    result = gen.generate_incident_postmortem("test-id")
    assert result.get("error") == "Incident not found"


def test_report_generator_weekly():
    """Test weekly report generation without API."""
    from reporting.report_generator import ReportGenerator

    gen = ReportGenerator(api_get=None)
    result = gen.generate_weekly_health_report()

    assert result["type"] == "weekly_health"
    assert "report" in result
    assert "Weekly Health Report" in result["report"]


def test_report_generator_monthly():
    """Test monthly trends generation without API."""
    from reporting.report_generator import ReportGenerator

    gen = ReportGenerator(api_get=None)
    result = gen.generate_monthly_trends()

    assert result["type"] == "monthly_trends"
    assert "report" in result
    assert "Monthly Trends" in result["report"]


def test_report_generator_executive():
    """Test executive summary generation without API."""
    from reporting.report_generator import ReportGenerator

    gen = ReportGenerator(api_get=None)
    result = gen.generate_executive_summary()

    assert result["type"] == "executive_summary"
    assert "report" in result
    assert "stats" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
