# Twitter/X Post

---

I built an AI-powered DevOps Assistant in 10 days

6 autonomous AI agents that:
- Monitor infrastructure 24/7
- Detect anomalies in real-time
- Diagnose root causes with Claude AI
- Auto-fix issues with safety guardrails
- Learn from every incident
- Predict problems before they happen

20K+ lines of code | 88 tests | Full stack

Tech: Next.js, FastAPI, PostgreSQL, Redis, Prometheus, Claude API, Qdrant, Docker, Slack

Thread with details

[GitHub link]

---

### Thread

1/ The Monitor Agent checks Prometheus every 30 seconds using z-score + moving average anomaly detection. When something looks off, it creates an incident.

2/ The Diagnostic Agent sends the incident context to Claude API for root cause analysis. But first, it checks a vector database — if a similar incident was seen before, it skips the API call.

3/ The Remediation Agent auto-fixes issues but with safety: checkpoints, rollback, circuit breaker. High-risk actions need human approval via Slack buttons.

4/ The Learning Agent stores patterns using sentence-transformer embeddings in Qdrant. The system literally gets smarter with every incident.

5/ The Prediction Agent uses time-series forecasting to warn you days before disk fills up or capacity runs out.

6/ Everything is production-ready: CI/CD, Docker, security headers, rate limiting, encryption, comprehensive tests.

Full code on GitHub: [link]
