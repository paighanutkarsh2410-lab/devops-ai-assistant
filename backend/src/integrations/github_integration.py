"""GitHub integration — link incidents to commits and deployments."""
import logging
import requests
from datetime import datetime, timedelta, timezone
from typing import Optional

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"


class GitHubIntegration:
    """Integrates with GitHub for commit linking and deployment tracking."""

    def __init__(self, config: dict):
        self.token = config.get("token", "")
        self.owner = config.get("owner", "")
        self.repo = config.get("repo", "")

    @property
    def available(self) -> bool:
        return bool(self.token and self.owner and self.repo)

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def _get(self, endpoint: str, params: dict = None) -> Optional[dict]:
        try:
            resp = requests.get(
                f"{GITHUB_API}{endpoint}",
                headers=self._headers(),
                params=params or {},
                timeout=10,
            )
            if resp.status_code == 200:
                return resp.json()
            logger.warning(f"GitHub API {resp.status_code}: {resp.text[:200]}")
            return None
        except Exception as e:
            logger.error(f"GitHub API error: {e}")
            return None

    def _post(self, endpoint: str, data: dict) -> Optional[dict]:
        try:
            resp = requests.post(
                f"{GITHUB_API}{endpoint}",
                headers=self._headers(),
                json=data,
                timeout=10,
            )
            if resp.status_code in (200, 201):
                return resp.json()
            logger.warning(f"GitHub API {resp.status_code}: {resp.text[:200]}")
            return None
        except Exception as e:
            logger.error(f"GitHub API error: {e}")
            return None

    def get_recent_commits(self, since: str = None, limit: int = 10) -> dict:
        """Get recent commits from the repository."""
        if not self.available:
            return {"success": False, "error": "GitHub not configured"}

        params = {"per_page": min(limit, 100)}
        if since:
            params["since"] = since

        data = self._get(f"/repos/{self.owner}/{self.repo}/commits", params)
        if data is None:
            return {"success": False, "error": "Failed to fetch commits"}

        commits = [
            {
                "sha": c["sha"][:7],
                "full_sha": c["sha"],
                "message": c["commit"]["message"].split("\n")[0],
                "author": c["commit"]["author"]["name"],
                "date": c["commit"]["author"]["date"],
                "url": c["html_url"],
            }
            for c in data
        ]

        return {
            "success": True,
            "repo": f"{self.owner}/{self.repo}",
            "commits": commits,
            "count": len(commits),
        }

    def get_recent_deployments(self, limit: int = 10) -> dict:
        """Get recent deployments (GitHub Deployments API or workflow runs)."""
        if not self.available:
            return {"success": False, "error": "GitHub not configured"}

        # Try workflow runs first (more commonly used than Deployments API)
        data = self._get(
            f"/repos/{self.owner}/{self.repo}/actions/runs",
            {"per_page": min(limit, 30), "status": "completed"},
        )

        if data and data.get("workflow_runs"):
            runs = [
                {
                    "id": r["id"],
                    "name": r["name"],
                    "status": r["conclusion"],
                    "branch": r["head_branch"],
                    "commit_sha": r["head_sha"][:7],
                    "created_at": r["created_at"],
                    "url": r["html_url"],
                }
                for r in data["workflow_runs"][:limit]
            ]
            return {"success": True, "deployments": runs, "count": len(runs)}

        # Fallback to Deployments API
        data = self._get(f"/repos/{self.owner}/{self.repo}/deployments", {"per_page": limit})
        if data is None:
            return {"success": True, "deployments": [], "count": 0}

        deployments = [
            {
                "id": d["id"],
                "environment": d.get("environment", "unknown"),
                "commit_sha": d["sha"][:7],
                "created_at": d["created_at"],
                "description": d.get("description", ""),
            }
            for d in data
        ]
        return {"success": True, "deployments": deployments, "count": len(deployments)}

    def link_incident_to_commit(self, incident_id: str, commit_sha: str) -> dict:
        """Link an incident to a specific commit by adding a comment."""
        if not self.available:
            return {"success": False, "error": "GitHub not configured"}

        # Get commit details
        commit_data = self._get(f"/repos/{self.owner}/{self.repo}/commits/{commit_sha}")
        if commit_data is None:
            return {"success": False, "error": f"Commit {commit_sha} not found"}

        return {
            "success": True,
            "incident_id": incident_id,
            "commit_sha": commit_sha[:7],
            "commit_message": commit_data["commit"]["message"].split("\n")[0],
            "commit_author": commit_data["commit"]["author"]["name"],
            "commit_date": commit_data["commit"]["author"]["date"],
            "commit_url": commit_data["html_url"],
        }

    def create_issue(self, title: str, body: str, labels: list = None) -> dict:
        """Create a GitHub issue from an incident."""
        if not self.available:
            return {"success": False, "error": "GitHub not configured"}

        data = self._post(
            f"/repos/{self.owner}/{self.repo}/issues",
            {
                "title": title,
                "body": body,
                "labels": labels or ["incident", "auto-created"],
            },
        )

        if data is None:
            return {"success": False, "error": "Failed to create issue"}

        return {
            "success": True,
            "issue_number": data["number"],
            "issue_url": data["html_url"],
            "title": data["title"],
        }

    def correlate_deployments(self, since: str, service_name: str = None) -> dict:
        """Find commits/deployments that may correlate with an incident timeframe."""
        if not self.available:
            return {"success": False, "error": "GitHub not configured"}

        commits_result = self.get_recent_commits(since=since, limit=20)
        deployments_result = self.get_recent_deployments(limit=10)

        recent_commits = commits_result.get("commits", [])
        recent_deployments = deployments_result.get("deployments", [])

        # Filter commits around the incident time
        suspect_commits = []
        if since:
            try:
                incident_time = datetime.fromisoformat(since.replace("Z", "+00:00"))
                window_start = incident_time - timedelta(hours=2)
                for c in recent_commits:
                    commit_time = datetime.fromisoformat(c["date"].replace("Z", "+00:00"))
                    if window_start <= commit_time <= incident_time:
                        suspect_commits.append(c)
            except (ValueError, KeyError):
                suspect_commits = recent_commits[:5]
        else:
            suspect_commits = recent_commits[:5]

        return {
            "success": True,
            "suspect_commits": suspect_commits,
            "recent_deployments": recent_deployments[:5],
            "correlation_window": "2 hours before incident",
            "repo": f"{self.owner}/{self.repo}",
        }

    def get_repo_info(self) -> dict:
        """Get basic repository information."""
        if not self.available:
            return {"success": False, "error": "GitHub not configured"}

        data = self._get(f"/repos/{self.owner}/{self.repo}")
        if data is None:
            return {"success": False, "error": "Failed to fetch repo info"}

        return {
            "success": True,
            "name": data["full_name"],
            "description": data.get("description", ""),
            "default_branch": data["default_branch"],
            "open_issues": data["open_issues_count"],
            "language": data.get("language", ""),
            "updated_at": data["updated_at"],
            "url": data["html_url"],
        }

    def test_connection(self) -> dict:
        """Test GitHub API connectivity."""
        if not self.available:
            return {"connected": False, "error": "Missing configuration"}

        data = self._get(f"/repos/{self.owner}/{self.repo}")
        if data is None:
            return {"connected": False, "error": "Cannot reach repository"}

        return {
            "connected": True,
            "repo": data["full_name"],
            "permissions": data.get("permissions", {}),
        }
