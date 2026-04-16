# Dev.to Post

---

**Title**: Building an AI DevOps Assistant with 6 Autonomous Agents (Full Stack Project)

**Tags**: #python #devops #ai #webdev

**Cover image**: Architecture diagram

---

## Introduction

I built an AI-powered DevOps assistant that automatically monitors infrastructure, diagnoses issues, and fixes them — using 6 coordinated AI agents.

In this post, I'll walk through the architecture, key decisions, and what I learned building it.

## The Pipeline

```
Monitor (30s) → Diagnose (60s) → Remediate (90s) → Learn (2min) → Predict (1hr) → Communicate (5min)
```

Each agent runs independently on a timer, communicating through Redis pub/sub events. If one agent crashes, the others keep running.

## Technical Highlights

### Smart Diagnosis
The Diagnostic Agent checks a vector database first — if a similar incident has been solved before (>85% match), it reuses the learned diagnosis instead of calling the LLM. This saves API costs and speeds up resolution.

### Safety-First Remediation
Every auto-fix goes through: checkpoint → execute → verify → rollback-if-failed. High-risk actions (like service restarts in production) require human approval via Slack buttons.

### The Learning Loop
After every resolved incident, the Learning Agent stores the pattern (symptoms, cause, solution) as a vector embedding. Over time, diagnosis accuracy improves and the system relies less on expensive LLM calls.

## Stack

| Component | Technology |
|-----------|-----------|
| Frontend | Next.js, Tailwind CSS |
| Backend | FastAPI, SQLAlchemy |
| Database | PostgreSQL, Redis |
| Monitoring | Prometheus, Grafana |
| AI | Claude API, Groq |
| Vector DB | Qdrant |
| Notifications | Slack, Resend |
| CI/CD | GitHub Actions, Docker |

## What I Learned

1. **Design for degradation** — Every external dependency (LLM, Slack, Qdrant) has a fallback
2. **Safety beats speed** — The approval workflow for high-risk actions is essential
3. **Test with real keys** — Mocked tests miss real integration issues
4. **Vector search is powerful** — Finding similar past incidents saves huge amounts of LLM cost

## Try It

The full source code is on GitHub: [link]

```bash
docker compose up -d
cd backend && python src/main.py
cd frontend && npm run dev
```

Feedback welcome!
