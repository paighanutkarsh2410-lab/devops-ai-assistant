"""API routes for the Agent Marketplace — browse, install, rate, publish."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

from models import get_db
from models.user import User
from utils.auth import get_current_user

router = APIRouter(prefix="/marketplace", tags=["marketplace"])

# ── Seed data ─────────────────────────────────────────────────────────

MARKETPLACE_ITEMS = [
    {
        "id": "aws-cloudwatch", "name": "AWS CloudWatch Connector", "type": "integration",
        "category": "Integrations", "author": "DevOps Community", "version": "2.1.0",
        "description": "Pull CloudWatch metrics and alarms into your monitoring pipeline. Supports EC2, RDS, Lambda, and custom namespaces.",
        "downloads": 1850, "rating": 4.6, "review_count": 42, "price": "free",
        "verified": True, "tags": ["aws", "cloudwatch", "metrics"],
        "config_template": {"region": "us-east-1", "namespace": "AWS/EC2", "period": 300},
        "installation_instructions": "1. Add AWS credentials\n2. Configure region and namespace\n3. Enable plugin",
        "screenshots": [], "dependencies": ["boto3"],
        "changelog": [{"version": "2.1.0", "date": "2024-01-10", "changes": ["Added Lambda support", "Fixed pagination bug"]}],
    },
    {
        "id": "pagerduty", "name": "PagerDuty Integration", "type": "integration",
        "category": "Integrations", "author": "PagerDuty", "version": "1.3.0",
        "description": "Two-way PagerDuty sync — incidents auto-create PD alerts, PD acks reflect in dashboard.",
        "downloads": 2340, "rating": 4.8, "review_count": 67, "price": "free",
        "verified": True, "tags": ["pagerduty", "alerting", "oncall"],
        "config_template": {"api_key": "", "service_id": "", "escalation_policy": ""},
        "installation_instructions": "1. Generate PagerDuty API key\n2. Enter service ID\n3. Map severity levels",
        "screenshots": [], "dependencies": [],
        "changelog": [{"version": "1.3.0", "date": "2024-01-05", "changes": ["Added escalation policy support"]}],
    },
    {
        "id": "k8s-healer", "name": "Kubernetes Auto-Healer", "type": "agent",
        "category": "Remediation Agents", "author": "K8s Experts", "version": "3.0.1",
        "description": "Advanced K8s remediation: pod eviction, node drain, HPA tuning, resource quota management.",
        "downloads": 3100, "rating": 4.7, "review_count": 89, "price": "free",
        "verified": True, "tags": ["kubernetes", "k8s", "auto-healing", "remediation"],
        "config_template": {"kubeconfig": "", "namespaces": ["default"], "dry_run": True},
        "installation_instructions": "1. Provide kubeconfig path\n2. Select namespaces\n3. Enable dry-run for testing",
        "screenshots": [], "dependencies": ["kubernetes"],
        "changelog": [{"version": "3.0.1", "date": "2024-01-08", "changes": ["Fixed HPA scaling race condition"]}],
    },
    {
        "id": "sql-analyzer", "name": "SQL Query Analyzer", "type": "plugin",
        "category": "Diagnostic Agents", "author": "DB Insights", "version": "1.2.0",
        "description": "Deep SQL query analysis with execution plan optimization, index suggestions, and deadlock detection.",
        "downloads": 980, "rating": 4.3, "review_count": 23, "price": "free",
        "verified": False, "tags": ["sql", "database", "performance", "diagnostic"],
        "config_template": {"connection_string": "", "slow_query_threshold_ms": 1000},
        "installation_instructions": "1. Provide database connection string\n2. Set slow query threshold\n3. Enable query logging",
        "screenshots": [], "dependencies": ["sqlparse"],
        "changelog": [],
    },
    {
        "id": "slack-rich", "name": "Slack Rich Notifications", "type": "plugin",
        "category": "Integrations", "author": "ChatOps Team", "version": "2.0.0",
        "description": "Rich Slack notifications with interactive buttons, thread updates, and incident resolution from Slack.",
        "downloads": 2100, "rating": 4.5, "review_count": 55, "price": "free",
        "verified": True, "tags": ["slack", "chatops", "notifications"],
        "config_template": {"webhook_url": "", "default_channel": "#incidents"},
        "installation_instructions": "1. Create Slack webhook\n2. Set default channel\n3. Configure notification templates",
        "screenshots": [], "dependencies": [],
        "changelog": [],
    },
    {
        "id": "cost-anomaly", "name": "Cost Anomaly Detector", "type": "agent",
        "category": "Diagnostic Agents", "author": "FinOps Team", "version": "1.4.0",
        "description": "ML-powered cloud cost anomaly detection with spend forecasting and budget alerts.",
        "downloads": 1400, "rating": 4.6, "review_count": 31, "price": "free",
        "verified": True, "tags": ["cost", "finops", "anomaly", "ml"],
        "config_template": {"cloud_provider": "aws", "budget_threshold": 1000},
        "installation_instructions": "1. Connect cloud billing API\n2. Set budget thresholds\n3. Configure alert channels",
        "screenshots": [], "dependencies": [],
        "changelog": [],
    },
    {
        "id": "terraform-drift", "name": "Terraform Drift Detector", "type": "plugin",
        "category": "Diagnostic Agents", "author": "IaC Labs", "version": "1.0.0",
        "description": "Detect Terraform state drift and suggest remediation plans. Supports AWS, GCP, Azure.",
        "downloads": 520, "rating": 4.1, "review_count": 12, "price": "free",
        "verified": False, "tags": ["terraform", "iac", "drift", "compliance"],
        "config_template": {"state_path": "", "providers": ["aws"]},
        "installation_instructions": "1. Point to Terraform state\n2. Configure providers\n3. Set scan schedule",
        "screenshots": [], "dependencies": [],
        "changelog": [],
    },
    {
        "id": "gh-actions-monitor", "name": "GitHub Actions Monitor", "type": "plugin",
        "category": "Integrations", "author": "CI/CD Community", "version": "1.0.2",
        "description": "Monitor GitHub Actions workflows, detect failures, auto-retry flaky builds.",
        "downloads": 890, "rating": 4.0, "review_count": 18, "price": "free",
        "verified": False, "tags": ["github", "ci-cd", "actions", "monitoring"],
        "config_template": {"github_token": "", "repos": [], "auto_retry": False},
        "installation_instructions": "1. Generate GitHub token\n2. Select repositories\n3. Enable auto-retry",
        "screenshots": [], "dependencies": [],
        "changelog": [],
    },
    {
        "id": "datadog-bridge", "name": "Datadog Bridge", "type": "plugin",
        "category": "Integrations", "author": "Monitoring Hub", "version": "1.1.0",
        "description": "Import Datadog metrics and monitors for unified observability alongside Prometheus.",
        "downloads": 750, "rating": 4.2, "review_count": 15, "price": "free",
        "verified": False, "tags": ["datadog", "metrics", "monitoring"],
        "config_template": {"api_key": "", "app_key": ""},
        "installation_instructions": "1. Provide Datadog API and App keys\n2. Select metrics to import\n3. Map tags",
        "screenshots": [], "dependencies": [],
        "changelog": [],
    },
    {
        "id": "incident-postmortem", "name": "Auto Postmortem Generator", "type": "workflow",
        "category": "Workflows", "author": "SRE Team", "version": "1.0.0",
        "description": "Automatically generate incident postmortems with timeline, root cause, and action items using AI.",
        "downloads": 1200, "rating": 4.4, "review_count": 28, "price": "free",
        "verified": True, "tags": ["postmortem", "incident", "documentation", "ai"],
        "config_template": {"template": "standard", "include_metrics": True},
        "installation_instructions": "1. Configure postmortem template\n2. Set auto-generation triggers\n3. Connect to documentation platform",
        "screenshots": [], "dependencies": [],
        "changelog": [],
    },
    {
        "id": "exec-dashboard-pack", "name": "Executive Dashboard Pack", "type": "dashboard",
        "category": "Dashboards", "author": "Analytics Team", "version": "2.0.0",
        "description": "Pre-built executive dashboards: SLA compliance, cost trends, incident velocity, team performance.",
        "downloads": 680, "rating": 4.5, "review_count": 19, "price": "free",
        "verified": True, "tags": ["dashboard", "executive", "reporting", "kpi"],
        "config_template": {"dashboards": ["sla", "cost", "incidents", "team"]},
        "installation_instructions": "1. Select dashboards to install\n2. Configure data sources\n3. Set refresh intervals",
        "screenshots": [], "dependencies": [],
        "changelog": [],
    },
    {
        "id": "weekly-report-template", "name": "Weekly SRE Report", "type": "report",
        "category": "Report Templates", "author": "SRE Community", "version": "1.2.0",
        "description": "Weekly SRE report template with automated metrics, incident summaries, and trend analysis.",
        "downloads": 940, "rating": 4.3, "review_count": 22, "price": "free",
        "verified": False, "tags": ["report", "sre", "weekly", "template"],
        "config_template": {"schedule": "monday_9am", "recipients": []},
        "installation_instructions": "1. Set report schedule\n2. Add recipients\n3. Customize sections",
        "screenshots": [], "dependencies": [],
        "changelog": [],
    },
]

CATEGORIES = [
    "Diagnostic Agents", "Remediation Agents", "Integrations",
    "Workflows", "Dashboards", "Report Templates",
]


@router.get("/items")
def browse_marketplace(
    category: Optional[str] = None,
    search: Optional[str] = None,
    item_type: Optional[str] = None,
    sort_by: str = Query("downloads", regex="^(downloads|rating|name)$"),
    verified_only: bool = False,
    user: User = Depends(get_current_user),
):
    items = list(MARKETPLACE_ITEMS)
    if category:
        items = [i for i in items if i["category"] == category]
    if item_type:
        items = [i for i in items if i["type"] == item_type]
    if search:
        q = search.lower()
        items = [i for i in items if q in i["name"].lower() or q in i["description"].lower()
                 or any(q in t for t in i.get("tags", []))]
    if verified_only:
        items = [i for i in items if i["verified"]]

    reverse = sort_by in ("downloads", "rating")
    items.sort(key=lambda i: i.get(sort_by, ""), reverse=reverse)

    return {"items": items, "total": len(items), "categories": CATEGORIES}


@router.get("/items/{item_id}")
def get_item(item_id: str, user: User = Depends(get_current_user)):
    item = next((i for i in MARKETPLACE_ITEMS if i["id"] == item_id), None)
    if not item:
        return {"error": "Item not found"}

    return {
        **item,
        "reviews": [
            {"user": "sre_lead", "rating": 5, "comment": "Works perfectly with our setup", "date": "2024-01-12"},
            {"user": "devops_eng", "rating": 4, "comment": "Good but docs could be better", "date": "2024-01-10"},
            {"user": "platform_team", "rating": 5, "comment": "Saved us hours of manual work", "date": "2024-01-08"},
        ],
    }


@router.post("/items/{item_id}/install")
def install_item(item_id: str, user: User = Depends(get_current_user)):
    item = next((i for i in MARKETPLACE_ITEMS if i["id"] == item_id), None)
    if not item:
        return {"error": "Item not found"}
    item["downloads"] = item.get("downloads", 0) + 1
    return {
        "status": "installed",
        "item": item["name"],
        "version": item["version"],
        "message": f"Successfully installed {item['name']} v{item['version']}",
        "next_steps": ["Configure settings", "Enable in agent dashboard", "Run test"],
    }


class ReviewCreate(BaseModel):
    rating: float
    comment: str = ""


@router.post("/items/{item_id}/rate")
def rate_item(item_id: str, body: ReviewCreate, user: User = Depends(get_current_user)):
    item = next((i for i in MARKETPLACE_ITEMS if i["id"] == item_id), None)
    if not item:
        return {"error": "Item not found"}

    count = item.get("review_count", 0)
    old_rating = item.get("rating", 0)
    item["rating"] = round((old_rating * count + body.rating) / (count + 1), 1)
    item["review_count"] = count + 1

    return {"status": "rated", "new_rating": item["rating"], "total_reviews": item["review_count"]}


class PublishItem(BaseModel):
    name: str
    description: str
    item_type: str
    category: str = "Integrations"
    version: str = "1.0.0"
    tags: List[str] = []
    config_template: dict = {}
    installation_instructions: str = ""


@router.post("/items")
def publish_item(body: PublishItem, user: User = Depends(get_current_user)):
    new_id = body.name.lower().replace(" ", "-")
    new_item = {
        "id": new_id, "name": body.name, "type": body.item_type,
        "category": body.category, "author": user.full_name or user.email,
        "version": body.version, "description": body.description,
        "downloads": 0, "rating": 0.0, "review_count": 0, "price": "free",
        "verified": False, "tags": body.tags,
        "config_template": body.config_template,
        "installation_instructions": body.installation_instructions,
        "screenshots": [], "dependencies": [], "changelog": [],
    }
    MARKETPLACE_ITEMS.append(new_item)
    return {"status": "published", "id": new_id, "message": "Item submitted for review"}
