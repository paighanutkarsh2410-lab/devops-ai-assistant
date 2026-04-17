# AI-Powered DevOps Assistant

An autonomous infrastructure monitoring and management platform built with 6 AI agents that work together to detect, diagnose, and remediate production issues in real-time.

## Overview

This platform automates the entire incident lifecycle — from anomaly detection to root cause analysis to automated remediation. It learns from every incident to improve over time and can predict issues before they impact users.

### Key Features

- **Real-time Monitoring** — Anomaly detection using z-score analysis, moving averages, and adaptive thresholds
- **AI-Powered Diagnostics** — Automated root cause analysis with correlation engine and knowledge base
- **Auto-Remediation** — Safe execution framework with checkpoints, rollback capability, and approval workflows
- **Predictive Analytics** — Time-series forecasting, capacity planning, and proactive alerting
- **Learning System** — Vector-based pattern recognition that improves diagnosis accuracy over time
- **Multi-Channel Notifications** — Intelligent alert routing with Slack, email, and in-app notifications
- **Natural Language Chat** — Ask questions about your infrastructure in plain English

## Architecture

```
                    ┌─────────────────────────────┐
                    │       Next.js Frontend       │
                    │    (Dashboard + Analytics)    │
                    └──────────┬──────────────────┘
                               │
                    ┌──────────▼──────────────────┐
                    │      FastAPI Backend         │
                    │   (REST API + WebSocket)     │
                    └──────────┬──────────────────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                     │
   ┌──────▼──────┐    ┌───────▼───────┐    ┌───────▼───────┐
   │ PostgreSQL  │    │    Redis      │    │  Anthropic    │
   │  Database   │    │    Cache      │    │     API       │
   └─────────────┘    └───────────────┘    └───────────────┘
```

### Agent Pipeline

```
Monitor → Diagnostic → Remediation → Learning → Prediction → Communication
```

Each agent operates autonomously and hands off context to the next stage. The pipeline processes incidents end-to-end without manual intervention.

## Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | Next.js 16, React 19, TypeScript |
| Backend | FastAPI, Python 3.12, SQLAlchemy |
| Database | PostgreSQL |
| Cache | Redis |
| AI/ML | Anthropic API, Sentence-Transformers |
| Hosting | Vercel (frontend), Render (backend) |
| Auth | JWT with bcrypt |

## Live Demo

- **App**: [devops-ai-assistant.vercel.app](https://devops-ai-assistant.vercel.app)
- **API**: [devops-ai-backend.onrender.com](https://devops-ai-backend.onrender.com)
- **API Docs**: [devops-ai-backend.onrender.com/docs](https://devops-ai-backend.onrender.com/docs)

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 20+
- PostgreSQL
- Redis

### Backend Setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
python src/main.py
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Environment Variables

Create a `.env` file in the backend directory:
```
DATABASE_URL=postgresql://user:pass@localhost:5432/devops_ai
REDIS_URL=redis://localhost:6379
ANTHROPIC_API_KEY=your_key_here
JWT_SECRET=your_secret_here
```

## Project Structure

```
devops-ai-assistant/
├── frontend/          # Next.js dashboard (35+ pages)
├── backend/           # FastAPI REST API
├── agents/            # AI agent pipeline
├── database/          # Schema and migrations
├── monitoring/        # Prometheus & Grafana configs
├── docs/              # Architecture and API documentation
├── tests/             # Test suites
└── security/          # Security audit and compliance
```

## Agent System

### Monitor Agent
Watches infrastructure metrics via Prometheus, detects anomalies using statistical analysis (z-score, moving averages), and triggers incidents when thresholds are breached.

### Diagnostic Agent
Investigates incidents by correlating metrics, deployments, and logs. Uses AI for root cause analysis with confidence scoring. Falls back to rule-based analysis when the API is unavailable.

### Remediation Agent
Executes safe automated fixes — service restarts, scaling, rollbacks, cache clearing. Every action has checkpoints and auto-rollback. High-risk actions require human approval.

### Learning Agent
Stores incident patterns in a vector database for similarity search. Tracks which remediation actions worked and recommends proven fixes for recurring issues.

### Prediction Agent
Forecasts metric trends using time-series analysis. Identifies capacity breaches before they happen and generates proactive alerts with prevention recommendations.

### Communication Agent
Routes notifications intelligently based on severity and user preferences. Supports Slack, email, and in-app channels with anti-spam protection.

## Dashboard Features

- Incident management with timeline and comments
- Real-time metric charts and live monitoring
- Predictive alerts with prevention tracking
- Approval workflow for remediation actions
- Audit log with full action history
- Runbook library and workflow automation
- Chaos engineering experiments
- SLA tracking and cost analysis
- Executive summary dashboards
- Custom report builder

## Safety & Security

- All remediation actions use checkpoint-based execution with automatic rollback
- Circuit breaker pattern prevents cascading failures from automated actions
- Human-in-the-loop approval for high-risk operations
- Complete audit trail of every automated action
- Rate limiting, input validation, and security headers

## License

MIT
