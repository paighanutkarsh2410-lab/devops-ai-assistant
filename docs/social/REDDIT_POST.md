# Reddit Post

**Subreddits**: r/devops, r/python, r/selfhosted, r/MachineLearning

---

**Title**: I built an AI-powered DevOps assistant with 6 autonomous agents — it monitors, diagnoses, fixes, learns, and predicts issues automatically

**Body**:

Hey everyone! I just finished building an AI-powered DevOps assistant and wanted to share it with the community.

**What it does:**

6 AI agents running in a pipeline, each with a specific job:

1. **Monitor Agent** (every 30s) — Polls Prometheus, runs anomaly detection (z-score, moving average, thresholds)
2. **Diagnostic Agent** (every 60s) — Uses Claude API for root cause analysis, correlates with deployments and past incidents
3. **Remediation Agent** (every 90s) — Auto-fixes issues with safety guardrails (checkpoints, rollback, circuit breaker, human approval for risky actions)
4. **Learning Agent** (every 2min) — Stores incident patterns in Qdrant vector DB, builds a knowledge base so the system gets smarter
5. **Prediction Agent** (every hour) — Time-series forecasting for capacity planning and cost prediction
6. **Communication Agent** (every 5min) — Smart Slack/email routing based on severity, with anti-spam

**Tech stack:**

- Next.js + Tailwind (frontend)
- FastAPI + SQLAlchemy (backend)
- PostgreSQL + Redis
- Prometheus + Grafana
- Claude API (Anthropic)
- Qdrant vector database
- Docker + GitHub Actions CI/CD

**Key stats:**
- ~20K lines of code
- 88 automated tests (all passing)
- 55+ API endpoints
- Full CRUD, auth, caching, rate limiting, security headers

GitHub: [link]

Would love feedback! What would you add?
