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
- [x] Day 5: Remediation Agent with safe execution, Docker/K8s integration, approval workflow, audit logging
- [x] Day 6: Learning Agent with vector KB, pattern recognition, feedback loops, recommendation engine
- [x] Day 7: Prediction Agent, time-series forecasting, capacity planning
- [x] Day 8: Communication Agent, Slack/email notifications, NL chat
- [x] Day 9: Optimization, security hardening, testing, UI polish
- [x] Day 10: Deployment, CI/CD, documentation, portfolio
- [x] Day 11: Advanced real-time features, collaboration, search, performance dashboard
- [x] Day 12: Advanced analytics engine, custom reports, trend analysis, SLA tracking, cost analytics, executive dashboard
- [x] Day 13: Custom workflows, smart escalation, incident runbooks, maintenance windows, integration marketplace, chaos engineering
- [x] Day 14: Advanced data visualizations (8 chart types), dark mode & theming (6 presets), UI components (command palette, data table, toast, modal), mobile-first responsive, accessibility (skip links, focus trap, ARIA), performance optimization (virtual list, caching, Web Vitals)
- [x] Day 15: Advanced agent orchestration (3 workflow patterns, agent registry), specialist agent library (7 domain experts), agent learning & adaptation (ELO scoring, A/B testing, strategy optimization), advanced pattern recognition (cascading failures, oscillation, degradation, correlation), explainable AI (evidence-ranked decisions, contrastive analysis, audit trail), agent performance optimization (TTL cache, batch processing, connection pooling, smart sampling, benchmarking)
- [x] Day 16: Plugin architecture (discovery, sandboxing, hot reload, marketplace), custom agent builder (no-code, templates, visual builder), agent marketplace (browse, install, rate, publish), collaboration protocols (request-response, broadcast, consensus, peer review, message bus), advanced remediation strategies (multi-step plans, conditional branching, retry, parallel execution, strategy library), agent monitoring & observability (health checks, SLA tracking, distributed tracing, structured logs), agent version management (semantic versioning, canary/blue-green deployment, A/B testing, rollback), testing framework (mock generators, scenario tests, load tests, chaos tests), documentation generator (AST-based, interactive docs page)
- [x] Day 17: Security audit (44-item checklist, vulnerability scanner), penetration testing (OWASP Top 10 coverage, 8 test suites, 29 tests), compliance framework (OWASP/GDPR/SOC 2/ISO 27001 scoring, gap analysis), audit logging (SHA-256 chain hashing, tamper detection), secrets management (Fernet encryption, rotation policies, audit trail), security monitoring (real-time threat detection, WAF with 8 rules, IP blocking), disaster recovery (DR plan, automated test framework, 23 DR tests, backup verification)
- [x] Day 18: Load testing (k6 scenarios: normal/stress/spike/soak, performance benchmarks, regression detection), chaos engineering (12 experiments, safety controls, game day scenarios, resilience scoring), E2E testing (Playwright: user flows, critical paths, visual regression, mobile, performance, accessibility), code quality (ESLint, pylint, pre-commit hooks, PR template, pyproject.toml), database optimization (query analyzer, index recommendations, vacuum scripts, connection pooling), final QA (automated checklist, QA automation suite)
- [x] Day 19-20: Feedback widget (in-app floating feedback form), LICENSE (MIT), GitHub issue templates (bug report, feature request), PR template, final polish and launch preparation

## Day 4: Diagnostic Agent

The AI-powered diagnostic system automatically investigates incidents:

- **Claude API Integration** — Structured root cause analysis with confidence scoring
- **Correlation Engine** — Links incidents to deployments, metric spikes, cascading failures
- **Knowledge Base** — TF-IDF similarity search over past incidents for pattern matching
- **Agent Orchestrator** — Manages Monitor + Diagnostic agents with Redis pub/sub events
- **Timeline Service** — Generates visual incident timelines with event correlation
- **Log & Deployment Tracking** — Full CRUD APIs for operational context

See [docs/DIAGNOSTIC_AGENT.md](docs/DIAGNOSTIC_AGENT.md) for architecture details.

## Day 5: Remediation Agent

Automated incident remediation with safety-first design:

- **Safe Execution Framework** — Checkpoints, auto-rollback, circuit breaker
- **Action Library** — 7 actions: restart, scale, rollback, cache clear, resource increase, kill process, rate limit
- **Docker & Kubernetes Integration** — Container management and pod orchestration
- **Strategy Engine** — Multi-step remediation plans for memory leaks, CPU spikes, timeouts, etc.
- **Approval Workflow** — Human-in-the-loop for HIGH risk actions
- **Impact Monitoring** — Before/after metric comparison with auto-rollback
- **Audit Trail** — Complete logging of every action taken
- **Full Pipeline** — Monitor → Diagnose → Remediate (all 3 agents)

See [docs/REMEDIATION_AGENT.md](docs/REMEDIATION_AGENT.md) and [docs/SAFETY_FRAMEWORK.md](docs/SAFETY_FRAMEWORK.md) for details.

## Day 6: Learning Agent

System that learns from every incident and gets smarter over time:

- **Qdrant Vector Database** — Stores incident embeddings for fast similarity search
- **Sentence-Transformers** — all-MiniLM-L6-v2 (384-dim) embeddings with Redis caching
- **Pattern Recognition** — 9 pattern types with DBSCAN clustering and trend detection
- **Feedback Loop** — Auto-tunes detection thresholds, action preferences, and baselines
- **Recommendation Engine** — Ranks actions by (similarity * success_rate * speed)
- **Correlation Matrix** — Symptom → Cause → Solution mappings with confidence scores
- **Agent Integration** — Diagnostic skips LLM if learned diagnosis found (>85% match)
- **Learning Dashboard** — Weekly reports, pattern insights, action effectiveness

See [docs/LEARNING_AGENT.md](docs/LEARNING_AGENT.md) for architecture details.

## Day 7: Prediction Agent

Proactive issue prevention through forecasting and capacity planning:

- **Prophet Forecasting** — Time-series prediction with daily/weekly seasonality (linear regression fallback)
- **Capacity Planning** — Predicts capacity breaches, recommends scaling, plans for events (e.g., Black Friday)
- **Trend Detection** — Linear regression + moving averages to spot degrading metrics early
- **Cost Forecasting** — Per-service cost breakdown, monthly projections, optimization recommendations
- **Predictive Alerts** — Lower urgency, prevention-focused alerts with suggested actions
- **Priority Scoring** — Ranks alerts by (time_urgency × severity × confidence)
- **Prevention Tracking** — Mark alerts as prevented, track prevention rate
- **5-Agent Pipeline** — Monitor → Diagnose → Remediate → Learn → Predict (complete)

See [docs/PREDICTION_AGENT.md](docs/PREDICTION_AGENT.md) for architecture details.

## Day 8: Communication Agent

Multi-channel notification system with intelligent routing:

- **Slack Integration** — Rich messages with interactive Approve/Reject buttons, thread replies, daily summaries
- **Email Notifications** — HTML templates via Resend API: incident alerts, critical urgents, weekly digests
- **Communication Agent** — Smart routing by severity, anti-spam (dedup, rate limits, quiet hours)
- **Natural Language Chat** — Ask questions in English: "Why is the API slow?" → AI-powered answers from system data
- **Report Generation** — Auto post-mortems, weekly health, monthly trends, executive summaries
- **Notification Preferences** — Per-channel settings, severity thresholds, service subscriptions, quiet hours
- **6-Agent Pipeline** — Monitor → Diagnose → Remediate → Learn → Predict → Communicate (complete)

See [docs/NOTIFICATIONS.md](docs/NOTIFICATIONS.md) for architecture details.

## Day 9: Optimization & Polish

Production-ready hardening across all layers:

- **Database Optimization** — Connection pooling (5-20), composite indexes on all hot queries, data archival with retention policies
- **API Performance** — Redis response caching (5min metrics, 1hr predictions), GZip compression, rate limiting (200 req/hr/IP)
- **Security Hardening** — CSP/HSTS/X-Frame headers, input validation & sanitization, Fernet encryption for sensitive fields, password policy enforcement
- **Frontend Optimization** — Error boundaries, skeleton loaders, empty states, accessibility (ARIA labels)
- **Comprehensive Testing** — Backend API tests (auth, incidents, alerts, middleware, security), load testing with Locust, agent tests (55+ passing)
- **Monitoring & Observability** — Health checker (DB, Redis, Prometheus, Claude API), system health dashboard, structured logging
- **UI/UX Polish** — Design system tokens, dark mode support, theme toggle, consistent component library
- **Documentation** — Architecture diagrams, deployment guide, user guide, developer guide, troubleshooting

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md), [docs/USER_GUIDE.md](docs/USER_GUIDE.md), [docs/DEVELOPER.md](docs/DEVELOPER.md).

## Day 10: Deployment & Launch

Production deployment and portfolio materials:

- **Production Docker Compose** — Multi-container setup with health checks, restart policies, persistent volumes
- **Dockerfiles** — Backend (FastAPI + Uvicorn), Agents (Python 3.12), Frontend (Next.js multi-stage build)
- **CI/CD Pipeline** — GitHub Actions: test on push, deploy staging on develop, deploy production on main with auto-rollback
- **Oracle Cloud Setup** — 2-VM architecture guide, SSL with Let's Encrypt, Nginx reverse proxy, firewall rules
- **Backup & Recovery** — Automated daily backups (7-day retention), rollback scripts
- **Portfolio Materials** — Blog post, LinkedIn post, presentation slides, demo video script, social media posts
- **Contributing Guide** — PR process, code style, issue templates (bug report, feature request)
- **Roadmap** — 4 phases: Team Features → Advanced AI → Enterprise → Platform

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md), [docs/ROADMAP.md](docs/ROADMAP.md), [CONTRIBUTING.md](CONTRIBUTING.md).

### Safety Warnings

```
Start with DRY RUN mode: python src/main.py --dry-run
Test on non-critical services first
Keep auto-remediation DISABLED initially
Require approval for ALL actions at first
```
