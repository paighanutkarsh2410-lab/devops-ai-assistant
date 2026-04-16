"""
Plugin Registry: Central catalog of all plugins with querying, metrics, and marketplace integration.
"""
import logging
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

from .plugin_system import PluginSystem, PluginType, PluginMetadata

logger = logging.getLogger(__name__)


@dataclass
class PluginMetrics:
    total_executions: int = 0
    total_errors: int = 0
    avg_duration_ms: float = 0.0
    last_executed: Optional[str] = None
    rating: float = 0.0
    review_count: int = 0
    downloads: int = 0


@dataclass
class MarketplaceEntry:
    name: str
    version: str
    author: str
    description: str
    plugin_type: str
    tags: List[str] = field(default_factory=list)
    rating: float = 0.0
    downloads: int = 0
    price: str = "free"
    install_url: str = ""
    verified: bool = False


class PluginRegistry:
    """
    Central registry for all plugins — local and marketplace.
    Supports querying by capability, on-demand loading, and per-plugin metrics.
    """

    def __init__(self, plugin_system: Optional[PluginSystem] = None):
        self._system = plugin_system or PluginSystem()
        self._metrics: Dict[str, PluginMetrics] = {}
        self._marketplace: List[MarketplaceEntry] = self._seed_marketplace()
        self._installed: Dict[str, str] = {}  # name → version
        self._lock = threading.Lock()

    # ── Registration ──────────────────────────────────────────────────

    def register(self, name: str) -> bool:
        """Load and register a plugin."""
        if self._system.load_plugin(name):
            self._system.initialize_plugin(name)
            with self._lock:
                self._metrics[name] = PluginMetrics()
            return True
        return False

    def unregister(self, name: str) -> bool:
        self._system.unload_plugin(name)
        with self._lock:
            self._metrics.pop(name, None)
        return True

    # ── Execution ─────────────────────────────────────────────────────

    def execute(self, name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a plugin and track metrics."""
        import time
        start = time.time()
        result = self._system.execute_plugin(name, context)
        duration = (time.time() - start) * 1000

        with self._lock:
            m = self._metrics.get(name)
            if m:
                m.total_executions += 1
                if "error" in result:
                    m.total_errors += 1
                m.avg_duration_ms = (
                    (m.avg_duration_ms * (m.total_executions - 1) + duration) / m.total_executions
                )
                m.last_executed = datetime.now(timezone.utc).isoformat()

        return result

    # ── Querying ──────────────────────────────────────────────────────

    def query_by_capability(self, capability: str) -> List[str]:
        return self._system.get_plugins_by_capability(capability)

    def query_by_type(self, plugin_type: PluginType) -> List[str]:
        return self._system.get_plugins_by_type(plugin_type)

    def get_info(self, name: str) -> Optional[Dict[str, Any]]:
        info = self._system.get_plugin_info(name)
        if info:
            m = self._metrics.get(name)
            if m:
                info["metrics"] = {
                    "total_executions": m.total_executions,
                    "total_errors": m.total_errors,
                    "avg_duration_ms": round(m.avg_duration_ms, 1),
                    "last_executed": m.last_executed,
                    "rating": m.rating,
                    "downloads": m.downloads,
                }
        return info

    def list_all(self) -> List[Dict[str, Any]]:
        return [self.get_info(n) for n in self._system._plugins if self.get_info(n)]

    # ── Marketplace ───────────────────────────────────────────────────

    def browse_marketplace(self, category: Optional[str] = None,
                           search: Optional[str] = None,
                           sort_by: str = "downloads") -> List[Dict[str, Any]]:
        items = list(self._marketplace)
        if category:
            items = [i for i in items if i.plugin_type == category]
        if search:
            q = search.lower()
            items = [i for i in items if q in i.name.lower() or q in i.description.lower()]

        key_map = {
            "downloads": lambda i: -i.downloads,
            "rating": lambda i: -i.rating,
            "name": lambda i: i.name,
        }
        items.sort(key=key_map.get(sort_by, key_map["downloads"]))

        return [
            {
                "name": i.name,
                "version": i.version,
                "author": i.author,
                "description": i.description,
                "type": i.plugin_type,
                "tags": i.tags,
                "rating": i.rating,
                "downloads": i.downloads,
                "price": i.price,
                "verified": i.verified,
                "installed": i.name in self._installed,
            }
            for i in items
        ]

    def install_from_marketplace(self, name: str) -> Dict[str, Any]:
        """Install a plugin from the marketplace."""
        entry = next((i for i in self._marketplace if i.name == name), None)
        if not entry:
            return {"error": "Item not found in marketplace"}

        self._installed[name] = entry.version
        entry.downloads += 1

        return {
            "status": "installed",
            "name": name,
            "version": entry.version,
            "message": f"Successfully installed {name} v{entry.version}",
        }

    def rate_plugin(self, name: str, rating: float, review: str = "") -> Dict[str, Any]:
        entry = next((i for i in self._marketplace if i.name == name), None)
        m = self._metrics.get(name)
        if entry:
            count = m.review_count if m else 0
            old_rating = entry.rating
            entry.rating = round((old_rating * count + rating) / (count + 1), 1)
            if m:
                m.review_count += 1
                m.rating = entry.rating
        return {"name": name, "new_rating": entry.rating if entry else 0}

    def _seed_marketplace(self) -> List[MarketplaceEntry]:
        """Seed marketplace with example entries."""
        return [
            MarketplaceEntry(
                name="aws-cloudwatch-connector", version="2.1.0", author="DevOps Community",
                description="Pull CloudWatch metrics and alarms into your monitoring pipeline",
                plugin_type="data_source", tags=["aws", "cloudwatch", "metrics"],
                rating=4.6, downloads=1850, verified=True,
            ),
            MarketplaceEntry(
                name="pagerduty-integration", version="1.3.0", author="PagerDuty",
                description="Two-way PagerDuty sync for incidents and escalations",
                plugin_type="integration", tags=["pagerduty", "alerting", "oncall"],
                rating=4.8, downloads=2340, verified=True,
            ),
            MarketplaceEntry(
                name="jira-ticket-creator", version="1.5.2", author="Atlassian Community",
                description="Auto-create Jira tickets from incidents with AI-generated descriptions",
                plugin_type="integration", tags=["jira", "ticketing", "automation"],
                rating=4.4, downloads=1620, verified=True,
            ),
            MarketplaceEntry(
                name="kubernetes-healer", version="3.0.1", author="K8s Experts",
                description="Advanced K8s remediation: pod eviction, node drain, HPA tuning",
                plugin_type="remediation", tags=["kubernetes", "k8s", "auto-healing"],
                rating=4.7, downloads=3100, verified=True,
            ),
            MarketplaceEntry(
                name="sql-query-analyzer", version="1.2.0", author="DB Insights",
                description="Deep SQL query analysis with execution plan optimization suggestions",
                plugin_type="diagnostic", tags=["sql", "database", "performance"],
                rating=4.3, downloads=980, verified=False,
            ),
            MarketplaceEntry(
                name="slack-rich-notifications", version="2.0.0", author="ChatOps Team",
                description="Rich Slack notifications with interactive buttons and thread updates",
                plugin_type="notification", tags=["slack", "chatops", "notifications"],
                rating=4.5, downloads=2100, verified=True,
            ),
            MarketplaceEntry(
                name="datadog-bridge", version="1.1.0", author="Monitoring Hub",
                description="Import Datadog metrics and monitors for unified observability",
                plugin_type="data_source", tags=["datadog", "metrics", "monitoring"],
                rating=4.2, downloads=750, verified=False,
            ),
            MarketplaceEntry(
                name="terraform-drift-detector", version="1.0.0", author="IaC Labs",
                description="Detect Terraform state drift and suggest remediation plans",
                plugin_type="diagnostic", tags=["terraform", "iac", "drift"],
                rating=4.1, downloads=520, verified=False,
            ),
            MarketplaceEntry(
                name="cost-anomaly-detector", version="1.4.0", author="FinOps Team",
                description="ML-powered cloud cost anomaly detection with spend forecasting",
                plugin_type="diagnostic", tags=["cost", "finops", "anomaly"],
                rating=4.6, downloads=1400, verified=True,
            ),
            MarketplaceEntry(
                name="github-actions-monitor", version="1.0.2", author="CI/CD Community",
                description="Monitor GitHub Actions workflows, detect failures, auto-retry",
                plugin_type="integration", tags=["github", "ci-cd", "actions"],
                rating=4.0, downloads=890, verified=False,
            ),
        ]

    @property
    def stats(self) -> Dict[str, Any]:
        return {
            "registered_plugins": len(self._metrics),
            "marketplace_items": len(self._marketplace),
            "installed_from_marketplace": len(self._installed),
            "total_executions": sum(m.total_executions for m in self._metrics.values()),
        }
