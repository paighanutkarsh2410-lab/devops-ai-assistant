# SentryAI

An autonomous infrastructure monitoring and management platform built with 8 AI agents that work together to detect, diagnose, and remediate production issues in real-time.

<div align="center">

### Introducing SentryAI

[![SentryAI — Promo Video](https://img.youtube.com/vi/pbmYtUhJ1SM/maxresdefault.jpg)](https://youtu.be/pbmYtUhJ1SM)

*Click to watch the promotional video*

**[Live App](https://devops-ai-assistant.vercel.app)** · **[API Docs](https://devops-ai-backend.onrender.com/docs)** · **[Architecture](#architecture)**

</div>

---

## Overview

This platform automates the entire incident lifecycle — from anomaly detection to root cause analysis to automated remediation. It learns from every incident to improve over time and can predict issues before they impact users.

### Key Features

- **Real-time Monitoring** — Anomaly detection using z-score analysis, moving averages, and adaptive thresholds
- **AI-Powered Diagnostics** — Automated root cause analysis with Claude AI, confidence scoring, and evidence chains
- **Auto-Remediation** — Safe execution framework with checkpoints, rollback capability, and approval workflows
- **Predictive Analytics** — Time-series forecasting, capacity planning, and proactive alerting
- **Learning System** — Qdrant vector-based pattern recognition that improves diagnosis accuracy over time
- **Multi-Channel Notifications** — Slack, email, and browser audio alerts with intelligent routing
- **Natural Language Chat** — Ask questions about your infrastructure in plain English
- **Real Integrations** — GitHub (commits, deployments, CI status), Slack (webhook notifications)
- **What-If Simulator** — Test incident response scenarios before they happen
- **Incident Flow Visualization** — Animated pipeline showing how 8 agents collaborate to resolve issues

### Screenshots

<details>
<summary>📊 Dashboard & Monitoring</summary>

| Dashboard | Live Metrics |
|:---------:|:------------:|
| Real-time overview with health scores, incident stats, and agent status | Live metric charts with anomaly detection overlays |

</details>

<details>
<summary>🤖 AI Agents</summary>

| Decision Graph | Incident Flow |
|:--------------:|:-------------:|
| Live visualization of agent communication and decision-making | Animated step-by-step pipeline showing agent collaboration |

</details>

<details>
<summary>🔮 Scenarios & Predictions</summary>

| What-If Simulator | Predictions |
|:------------------:|:-----------:|
| Simulate infrastructure incidents and see agent responses | Forecasted issues with prevention recommendations |

</details>

---

## Architecture

```
                    ┌─────────────────────────────┐
                    │       Next.js Frontend       │
                    │   (28+ Dashboard Sections)   │
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
   │ PostgreSQL  │    │    Redis      │    │  Claude AI    │
   │  Database   │    │    Cache      │    │  (Anthropic)  │
   └─────────────┘    └───────────────┘    └───────────────┘
```

### Agent Pipeline

```
Monitor → Diagnostic → Log Analysis → Remediation → Learning → Prediction → Capacity → Communication
  30s        60s          120s           90s          120s       hourly       30min       5min
```

Each agent operates autonomously with its own tick interval and hands off context to the next stage. The pipeline processes incidents end-to-end without manual intervention.

## Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | Next.js 16, React 19, TypeScript, Canvas API |
| Backend | FastAPI, Python 3.12, SQLAlchemy |
| Database | PostgreSQL |
| Cache | Redis |
| AI/ML | Claude API (Anthropic), Sentence-Transformers |
| Vector DB | Qdrant Cloud |
| Integrations | GitHub API, Slack Webhooks, Resend Email |
| Hosting | Vercel (frontend), Render (backend) |
| CI/CD | GitHub Actions |
| Auth | JWT with bcrypt |
| PWA | Service Worker, Web Audio API |

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
├── frontend/          # Next.js dashboard (28+ sections)
├── backend/           # FastAPI REST API
├── agents/            # AI agent pipeline (8 agents)
├── database/          # Schema and migrations
├── monitoring/        # Prometheus & Grafana configs
├── docs/              # Architecture and API documentation
├── .github/           # CI/CD workflows
└── security/          # Security audit and compliance
```

## Agent System

### Monitor Agent
Watches infrastructure metrics via Prometheus, detects anomalies using statistical analysis (z-score, moving averages), and triggers incidents when thresholds are breached. Runs every **30 seconds**.

### Diagnostic Agent
Investigates incidents by correlating metrics, deployments, and logs. Uses Claude AI for root cause analysis with confidence scoring and evidence chains. Falls back to rule-based analysis when the API is unavailable. Runs every **60 seconds**.

### Remediation Agent
Executes safe automated fixes — service restarts, scaling, rollbacks, cache clearing. Every action has checkpoints and auto-rollback. High-risk actions require human approval. Runs every **90 seconds**.

### Learning Agent
Stores incident patterns in Qdrant vector database for similarity search using sentence-transformer embeddings. Tracks which remediation actions worked and recommends proven fixes for recurring issues. Runs every **2 minutes**.

### Prediction Agent
Forecasts metric trends using time-series analysis (Prophet/linear regression). Identifies capacity breaches before they happen and generates proactive alerts with prevention recommendations. Runs **hourly**.

### Log Analysis Agent
Ingests application logs, detects error patterns using regex matching, clusters related errors, and uses Claude AI for intelligent root cause analysis. Generates actionable recommendations for each error category. Runs every **2 minutes**.

### Capacity Planning Agent
Tracks resource usage trends (CPU, memory, disk) over days/weeks using linear regression. Predicts when resources will reach warning/critical thresholds and recommends scaling decisions before exhaustion. Runs every **30 minutes**.

### Communication Agent
Routes notifications intelligently based on severity and user preferences. Supports Slack (rich messages, thread replies, interactive buttons), email, and browser audio alerts. Anti-spam with dedup, rate limiting, and quiet hours. Runs every **5 minutes**.

## Dashboard Features

| Category | Features |
|----------|----------|
| **Overview** | Dashboard, Live Metrics, AI Chat |
| **Monitoring** | System Health, Analytics, Performance, Predictions |
| **AI Agents** | Agent Status, Intelligence, Decision Graph, Incident Flow, Agent Builder, Marketplace, Learning |
| **Operations** | Workflows, Runbooks, Maintenance, Chaos Testing, What-If Scenarios, Post-Mortem Reviews, Log Analysis, Capacity Planning |
| **Security** | Security Dashboard, Compliance, Audit Log, Disaster Recovery |
| **Insights** | Reports, Cost Analysis, SLA Tracking, Executive View, Visualizations |
| **Settings** | Notifications (with audio alert test), Integrations, Theme |

## Key Integrations

- **GitHub** — Real-time commits, deployments, CI status, deployment correlation with incidents
- **Slack** — Rich incident notifications, remediation updates, approval requests, daily summaries
- **Browser Alerts** — Web Audio API alarm sounds for critical/high severity incidents (no sound files needed)
- **PWA** — Installable on mobile, network-first caching, auto-update on deploy

## Safety & Security

- All remediation actions use checkpoint-based execution with automatic rollback
- Circuit breaker pattern prevents cascading failures from automated actions
- Human-in-the-loop approval for high-risk operations
- Complete audit trail of every automated action
- Rate limiting, input validation, and security headers

## License

MIT
