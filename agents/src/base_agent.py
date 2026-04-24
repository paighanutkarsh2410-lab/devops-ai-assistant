import requests
import time
from config import BACKEND_URL, AGENT_EMAIL, AGENT_PASSWORD


class BaseAgent:
    """Base class for all AI agents."""

    def __init__(self, name: str):
        self.name = name
        self.token = None
        self.running = False

    def authenticate(self):
        """Login to backend and get JWT token. Auto-signup if needed."""
        # Try signup first (ignore if already exists)
        try:
            requests.post(f"{BACKEND_URL}/auth/signup", json={
                "email": AGENT_EMAIL,
                "password": AGENT_PASSWORD,
                "full_name": f"Monitor Agent ({self.name})",
                "company": "SentryAI System"
            }, timeout=5)
        except Exception:
            pass

        # Login
        resp = requests.post(f"{BACKEND_URL}/auth/login", json={
            "email": AGENT_EMAIL,
            "password": AGENT_PASSWORD
        }, timeout=5)
        resp.raise_for_status()
        self.token = resp.json()["access_token"]
        print(f"[{self.name}] Authenticated successfully")

    def _headers(self):
        return {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}

    def api_get(self, path: str, params: dict = None):
        resp = requests.get(f"{BACKEND_URL}{path}", headers=self._headers(), params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def api_post(self, path: str, data: dict):
        resp = requests.post(f"{BACKEND_URL}{path}", headers=self._headers(), json=data, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def run(self, interval: int = 30):
        """Main run loop."""
        self.running = True
        self.authenticate()
        print(f"[{self.name}] Starting (interval={interval}s)")

        while self.running:
            try:
                self.tick()
            except Exception as e:
                print(f"[{self.name}] Error: {e}")
                # Re-authenticate in case token expired
                try:
                    self.authenticate()
                except Exception:
                    pass
            time.sleep(interval)

    def tick(self):
        """Override in subclass. Called every interval."""
        raise NotImplementedError

    def stop(self):
        self.running = False
