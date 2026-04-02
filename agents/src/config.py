import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://localhost:9090")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
AGENT_EMAIL = os.getenv("AGENT_EMAIL", "agent@devops-ai.system")
AGENT_PASSWORD = os.getenv("AGENT_PASSWORD", "agent-secret-password-123")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
CHECK_INTERVAL_SECONDS = int(os.getenv("CHECK_INTERVAL_SECONDS", "30"))
ANOMALY_THRESHOLD = float(os.getenv("ANOMALY_THRESHOLD", "2.5"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
