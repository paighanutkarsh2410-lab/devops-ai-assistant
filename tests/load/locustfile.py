"""Load testing with Locust.

Usage:
  pip install locust
  locust -f tests/load/locustfile.py --host http://localhost:8000
  # Open http://localhost:8089 to configure and start
"""
from locust import HttpUser, task, between


class DevOpsUser(HttpUser):
    """Simulates a typical DevOps dashboard user."""
    wait_time = between(1, 3)
    token = None

    def on_start(self):
        """Login on start."""
        import uuid
        email = f"load-{uuid.uuid4().hex[:6]}@test.com"
        self.client.post("/auth/signup", json={
            "email": email,
            "password": "LoadTest1!",
        })
        resp = self.client.post("/auth/login", json={
            "email": email,
            "password": "LoadTest1!",
        })
        if resp.status_code == 200:
            self.token = resp.json().get("access_token")

    @property
    def headers(self):
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    @task(5)
    def view_dashboard(self):
        self.client.get("/incidents/", headers=self.headers)

    @task(3)
    def view_metrics(self):
        self.client.get("/metrics/", headers=self.headers)

    @task(2)
    def view_alerts(self):
        self.client.get("/alerts/", headers=self.headers)

    @task(1)
    def health_check(self):
        self.client.get("/health")

    @task(1)
    def view_predictions(self):
        self.client.get("/alerts/predictive/stats", headers=self.headers)

    @task(1)
    def create_incident(self):
        self.client.post("/incidents/", headers=self.headers, json={
            "title": "Load test incident",
            "severity": "low",
            "service_name": "load-test",
        })
