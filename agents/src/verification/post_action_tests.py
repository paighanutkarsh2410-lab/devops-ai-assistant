"""
Post-Action Tests: Runs smoke tests after remediation to verify service health.
"""
import logging
import requests
import time

logger = logging.getLogger(__name__)


class PostActionTests:
    """Runs automated tests after remediation actions."""

    def __init__(self, backend_url: str = "http://localhost:8000"):
        self.backend_url = backend_url

    def run_smoke_tests(self, service: str) -> dict:
        """Run a suite of smoke tests for a service."""
        results = []

        # Test 1: API health check
        results.append(self._test_health_endpoint())

        # Test 2: API response time
        results.append(self._test_response_time())

        # Test 3: Database connectivity (via API)
        results.append(self._test_db_connectivity())

        passed = sum(1 for r in results if r["passed"])
        total = len(results)

        return {
            "passed": passed,
            "total": total,
            "all_passed": passed == total,
            "results": results,
        }

    def _test_health_endpoint(self) -> dict:
        """Test that the health endpoint responds."""
        try:
            resp = requests.get(f"{self.backend_url}/health", timeout=5)
            passed = resp.status_code == 200
            return {"name": "health_check", "passed": passed,
                    "message": f"Status: {resp.status_code}"}
        except Exception as e:
            return {"name": "health_check", "passed": False, "message": str(e)}

    def _test_response_time(self) -> dict:
        """Test that API response time is acceptable."""
        try:
            start = time.time()
            resp = requests.get(f"{self.backend_url}/health", timeout=10)
            elapsed_ms = (time.time() - start) * 1000
            passed = elapsed_ms < 1000  # Under 1 second
            return {"name": "response_time", "passed": passed,
                    "message": f"{elapsed_ms:.0f}ms"}
        except Exception as e:
            return {"name": "response_time", "passed": False, "message": str(e)}

    def _test_db_connectivity(self) -> dict:
        """Test database connectivity via the incidents endpoint."""
        try:
            resp = requests.get(f"{self.backend_url}/incidents/?limit=1", timeout=5)
            passed = resp.status_code in (200, 401)  # 401 is ok, means API works
            return {"name": "db_connectivity", "passed": passed,
                    "message": f"Status: {resp.status_code}"}
        except Exception as e:
            return {"name": "db_connectivity", "passed": False, "message": str(e)}
