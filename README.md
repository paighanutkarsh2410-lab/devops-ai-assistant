# AI-Powered DevOps Assistant

Autonomous infrastructure monitoring and management system with AI agents.

## Project Structure

```
devops-ai-assistant/
├── frontend/          # Next.js dashboard
├── backend/           # FastAPI server
├── agents/            # AI agent logic
├── database/          # Database schemas and migrations
├── infrastructure/    # Docker configs
├── monitoring/        # Prometheus & Grafana configs
└── docs/             # Documentation
```

## Tech Stack

| Component | Technology |
|---|---|
| Cloud | Oracle Cloud / DigitalOcean |
| Containers | Docker + Docker Compose |
| Orchestration | Kubernetes (K3s) |
| Monitoring | Prometheus + Grafana |
| Logs | Loki + Promtail |
| AI Brain | Claude API |
| Fast AI | Groq |
| Vector DB | Qdrant Cloud |
| Database | PostgreSQL + TimescaleDB |
| Cache | Redis (Upstash) |
| Agent Framework | LangGraph |
| Frontend | Next.js + Vercel |
| Notifications | Slack / Discord |
| CI/CD | GitHub Actions |

## Getting Started

### Prerequisites
- Docker + Docker Compose
- Node.js 20+
- Python 3.10+

### Run Services
```bash
docker compose up -d
```

### Run Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
python src/main.py
```

### Run Frontend
```bash
cd frontend
npm install
npm run dev
```

## Services

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Grafana | http://localhost:3002 |
| Prometheus | http://localhost:9090 |

## Progress

- [x] Day 1: Project setup, Docker services, Frontend & Backend skeleton
- [x] Day 2: Database schema, Auth (JWT), API endpoints, Dashboard UI
- [x] Day 3: Prometheus monitoring, Anomaly detection (z-score, moving avg, threshold), WebSocket alerts, Alert dashboard
- [x] Day 4: Diagnostic Agent with Claude AI, Correlation Engine, Knowledge Base, Timeline, Log/Deployment APIs
- [ ] Day 5: Advanced alerting, notification channels
- [ ] Day 6: Kubernetes integration, auto-remediation
- [ ] Day 7: Final testing, deployment, UI overhaul

## Day 4: Diagnostic Agent

The AI-powered diagnostic system automatically investigates incidents:

- **Claude API Integration** — Structured root cause analysis with confidence scoring
- **Correlation Engine** — Links incidents to deployments, metric spikes, cascading failures
- **Knowledge Base** — TF-IDF similarity search over past incidents for pattern matching
- **Agent Orchestrator** — Manages Monitor + Diagnostic agents with Redis pub/sub events
- **Timeline Service** — Generates visual incident timelines with event correlation
- **Log & Deployment Tracking** — Full CRUD APIs for operational context

See [docs/DIAGNOSTIC_AGENT.md](docs/DIAGNOSTIC_AGENT.md) for architecture details.
