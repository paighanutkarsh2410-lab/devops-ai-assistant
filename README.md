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
- [ ] Day 2: Database schema, Auth, API endpoints, Dashboard UI
