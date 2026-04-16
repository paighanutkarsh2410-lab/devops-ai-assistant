# Deployment Guide

## Prerequisites

- Docker + Docker Compose
- Node.js 20+
- Python 3.10+
- PostgreSQL 15+
- Redis 7+

## Environment Variables

### Backend (.env)

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `REDIS_URL` | Redis connection string | Yes |
| `JWT_SECRET` | Secret key for JWT tokens | Yes |
| `CORS_ORIGINS` | Allowed frontend origins (comma-separated) | Yes |
| `ENCRYPTION_KEY` | Fernet key for field encryption | Recommended |

### Agents (agents/.env)

| Variable | Description | Required |
|----------|-------------|----------|
| `BACKEND_URL` | Backend API URL | Yes |
| `PROMETHEUS_URL` | Prometheus URL | Yes |
| `ANTHROPIC_API_KEY` | Claude API key | Yes |
| `GROQ_API_KEY` | Groq API key (fast AI) | Optional |
| `QDRANT_URL` | Qdrant vector DB URL | Optional |
| `QDRANT_API_KEY` | Qdrant API key | Optional |
| `SLACK_WEBHOOK_URL` | Slack incoming webhook | Optional |
| `SLACK_BOT_TOKEN` | Slack bot token | Optional |
| `RESEND_API_KEY` | Resend email API key | Optional |

## Quick Start

```bash
# 1. Start infrastructure
docker compose up -d

# 2. Start backend
cd backend
pip install -r requirements.txt
python src/main.py

# 3. Start frontend
cd frontend
npm install
npm run dev

# 4. Start agents (optional)
cd agents
pip install -r requirements.txt
python src/orchestrator.py
```

## Production Deployment

### Docker

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Database Migrations

```bash
cd database/migrations
psql -U devops_user -d devops_ai -f 001_add_indexes.sql
psql -U devops_user -d devops_ai -f 002_add_archive_tables.sql
```

### Rollback

```bash
psql -U devops_user -d devops_ai -f 001_add_indexes_rollback.sql
```

## Monitoring

| Service | URL | Purpose |
|---------|-----|---------|
| API Health | `/health` | Service health + deps |
| Prometheus | `:9090` | Metrics collection |
| Grafana | `:3002` | Dashboards |
| API Docs | `/docs` | Swagger UI |
| System Health | Frontend `/system-health` | UI health dashboard |

## Backup

```bash
# Database backup
pg_dump -U devops_user devops_ai > backup_$(date +%Y%m%d).sql

# Restore
psql -U devops_user devops_ai < backup_20260405.sql
```

## Data Retention

| Data | Retention | Action |
|------|-----------|--------|
| Metrics | 90 days | Archive to archived_metrics |
| Logs | 30 days | Delete |
| Alerts | 180 days | Delete (resolved only) |
| Incidents | Forever | Archive resolved after 365 days |
| Notifications | 90 days | Delete |
