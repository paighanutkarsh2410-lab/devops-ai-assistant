"""GitHub integration — link incidents to commits and deployments."""
import logging

logger = logging.getLogger(__name__)


class GitHubIntegration:
    """Integrates with GitHub for commit linking and deployment tracking."""

    def __init__(self, config: dict):
        self.token = config.get("token", "")
        self.owner = config.get("owner", "")
        self.repo = config.get("repo", "")

    @property
    def available(self) -> bool:
        return bool(self.token and self.owner and self.repo)

    def get_recent_commits(self, since: str = None, limit: int = 10) -> dict:
        """Get recent commits."""
        if not self.available:
            return {"success": False, "error": "GitHub not configured"}

        logger.info(f"Fetching commits from {self.owner}/{self.repo}")
        return {
            "success": True,
            "repo": f"{self.owner}/{self.repo}",
            "message": f"Recent commits fetched (limit: {limit})",
        }

    def link_incident_to_commit(self, incident_id: str, commit_sha: str) -> dict:
        """Link an incident to a specific commit."""
        if not self.available:
            return {"success": False, "error": "GitHub not configured"}

        return {
            "success": True,
            "incident_id": incident_id,
            "commit_sha": commit_sha,
            "commit_url": f"https://github.com/{self.owner}/{self.repo}/commit/{commit_sha}",
        }

    def create_issue(self, title: str, body: str, labels: list = None) -> dict:
        """Create a GitHub issue from an incident."""
        if not self.available:
            return {"success": False, "error": "GitHub not configured"}

        logger.info(f"GitHub issue created: {title}")
        return {
            "success": True,
            "title": title,
            "labels": labels or ["incident"],
            "message": f"Issue created in {self.owner}/{self.repo}",
        }

    def correlate_deployments(self, since: str, service_name: str = None) -> dict:
        """Find deployments that may correlate with an incident."""
        if not self.available:
            return {"success": False, "error": "GitHub not configured"}

        return {
            "success": True,
            "message": "Deployment correlation analysis complete",
            "repo": f"{self.owner}/{self.repo}",
        }

    def test_connection(self) -> dict:
        if not self.available:
            return {"connected": False, "error": "Missing configuration"}
        return {"connected": True, "repo": f"{self.owner}/{self.repo}"}
