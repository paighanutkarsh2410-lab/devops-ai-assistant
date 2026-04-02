# Diagnostic Agent

The Diagnostic Agent automatically investigates infrastructure incidents to determine root causes using AI-powered analysis.

## Architecture

```
Incident Created
    │
    ▼
┌─────────────────────┐
│  Diagnostic Agent   │
│                     │
│  1. Gather Context  │──► Metrics, Logs, Deployments
│  2. Knowledge Base  │──► TF-IDF Similarity Search
│  3. Correlations    │──► Deployment / Spike / Cascade
│  4. AI Analysis     │──► Claude API (with fallback)
│  5. Update Incident │──► Root cause + Actions
│  6. Store in KB     │──► For future matching
└─────────────────────┘
```

## Pipeline Steps

### 1. Gather Context
Collects recent metrics, error logs, and deployments for the affected service from the backend API.

### 2. Knowledge Base Search
Uses TF-IDF cosine similarity to find previously resolved incidents with similar characteristics. If a match scores above 0.8, it's used directly without calling the AI.

### 3. Correlation Engine
Analyzes four types of correlations:
- **Deployment correlation** (score: 90): Recent deployments on the affected service or its dependencies
- **Cascading failure** (score: 85): Dependent services also experiencing issues
- **Metric spikes** (score: 75): Abnormal CPU, memory, error rate, or response time
- **Time correlation** (score: 65): Multiple simultaneous incidents

### 4. AI Analysis
Sends all gathered context to Claude API for root cause analysis. Returns structured JSON with:
- `root_cause`: Primary cause description
- `confidence`: 0-100 confidence score
- `reasoning`: Step-by-step explanation
- `recommended_actions`: List of remediation steps
- `severity_assessment`: Severity level

If Claude API is unavailable, falls back to rule-based analysis using correlation results.

### 5. Update Incident
Patches the incident record with the diagnosis findings and sets status to "investigating".

### 6. Knowledge Base Storage
Stores the resolved incident for future similarity matching, building institutional memory.

## Service Dependencies

The correlation engine tracks known service dependencies:

```
api-gateway ──► auth-service, web-server-01
web-server-01 ──► database-primary, cache-redis
auth-service ──► database-primary, cache-redis
```

## Configuration

| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | (required) | Claude API key |
| `BACKEND_URL` | `http://localhost:8000` | Backend API URL |
| `REDIS_URL` | `redis://localhost:6379` | Redis for event pub/sub |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

## Running the Agent

```bash
cd agents
python src/main.py
```

Or with the start script:
```bash
./start.sh
```
