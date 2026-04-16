# Developer Guide

## Local Setup

```bash
# Clone
git clone <repo-url>
cd devops-ai-assistant

# Infrastructure
docker compose up -d  # PostgreSQL, Redis, Prometheus, Grafana

# Backend
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
python src/main.py

# Frontend
cd frontend
npm install
npm run dev

# Agents (optional)
cd agents
pip install -r requirements.txt
python src/orchestrator.py
```

## Project Structure

```
devops-ai-assistant/
├── frontend/                 # Next.js app
│   ├── app/                  # Pages (dashboard, chat, predictions, etc.)
│   ├── components/           # Reusable components
│   └── lib/                  # API clients, design system, utilities
├── backend/
│   └── src/
│       ├── main.py           # FastAPI app entry point
│       ├── routes/           # API endpoints
│       ├── models/           # SQLAlchemy models
│       ├── schemas/          # Pydantic schemas
│       ├── services/         # Business logic
│       ├── middleware/       # Cache, rate limit, security
│       ├── security/         # Encryption, validators
│       └── monitoring/       # Prometheus exporter
├── agents/
│   └── src/
│       ├── orchestrator.py   # Main agent coordinator
│       ├── monitor_agent.py  # Anomaly detection
│       ├── diagnostic_agent.py
│       ├── remediation_agent.py
│       ├── learning_agent.py
│       ├── prediction_agent.py
│       ├── communication_agent.py
│       ├── notifications/    # Slack + Email clients
│       ├── reporting/        # Report generation
│       ├── health/           # Health checker
│       └── safety/           # Execution framework
├── database/migrations/      # SQL migration scripts
├── tests/                    # Load tests, E2E tests
└── docs/                     # Documentation
```

## Running Tests

```bash
# Agent tests (Python 3.12)
cd agents
py -3.12 -m pytest tests/ -v

# Backend tests (requires running DB)
cd backend
py -3.12 -m pytest tests/ -v

# Load tests
pip install locust
locust -f tests/load/locustfile.py --host http://localhost:8000
```

## Code Style

- **Python**: PEP 8, type hints on public functions
- **TypeScript**: ESLint defaults from Next.js
- **Commits**: Descriptive messages, reference issue/day numbers

## Adding a New Agent

1. Create `agents/src/my_agent.py` extending `BaseAgent`
2. Implement `tick()` method for periodic work
3. Register in `orchestrator.py` (import, init, start thread)
4. Add events to `events.py`
5. Write tests in `agents/tests/test_my_agent.py`

## Adding a New API Endpoint

1. Create route file in `backend/src/routes/`
2. Add Pydantic schemas in `backend/src/schemas/`
3. Register router in `main.py`
4. Add API client method in `frontend/lib/api.ts`
5. Write tests in `backend/tests/test_api/`
