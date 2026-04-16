# How I Built an AI-Powered DevOps Assistant in 10 Days

## The Problem

Modern infrastructure generates thousands of alerts daily. DevOps teams are overwhelmed — spending more time firefighting than building. What if an AI system could monitor, diagnose, and fix infrastructure issues automatically?

That's what I set out to build.

## What I Built

An autonomous DevOps assistant with 6 AI agents working in a pipeline:

**Monitor → Diagnose → Remediate → Learn → Predict → Communicate**

Each agent runs on a timer, processing events and handing off to the next. The system watches Prometheus metrics, uses Claude API for intelligent root cause analysis, auto-fixes issues with safety guardrails, and learns from every incident to get smarter over time.

## The Architecture

The stack:
- **Frontend**: Next.js dashboard with real-time WebSocket updates
- **Backend**: FastAPI with PostgreSQL, Redis, and comprehensive API
- **AI Brain**: Claude API (Anthropic) for diagnosis and reporting
- **Monitoring**: Prometheus + Grafana for metrics collection
- **Vector DB**: Qdrant for similarity-based pattern matching
- **Notifications**: Slack (interactive buttons) + Email (Resend API)

## How the Agents Work

### Monitor Agent (every 30s)
Polls Prometheus and runs three anomaly detection algorithms: z-score analysis, moving average deviation, and threshold-based detection. When something looks wrong, it creates an incident and triggers the pipeline.

### Diagnostic Agent (every 60s)
The interesting one. It takes the incident context — current metrics, recent deployments, service logs — and sends a structured prompt to Claude API. The response includes root cause analysis, confidence scoring, and recommended actions.

But here's the clever part: before calling the LLM, it checks the Learning Agent's knowledge base. If a similar incident has been seen before with >85% similarity, it skips the expensive API call and uses the learned diagnosis.

### Remediation Agent (every 90s)
Executes fixes with a safety-first framework: checkpoints before every action, automatic rollback on failure, circuit breaker for repeated failures, and human approval for high-risk actions via Slack buttons.

### Learning Agent (every 120s)
After each incident resolves, it stores the pattern in Qdrant vector database using sentence-transformer embeddings. Over time, it builds a correlation matrix mapping symptoms → causes → solutions with confidence scores.

### Prediction Agent (every hour)
Uses time-series forecasting (Prophet with linear regression fallback) to predict capacity breaches, cost overruns, and trending issues before they become incidents.

### Communication Agent (every 5 min)
Routes notifications intelligently — critical goes to Slack + email immediately, medium to Slack only, low severity buffered for daily digest. Anti-spam with dedup, rate limiting, and quiet hours.

## Key Technical Decisions

**Why Claude API over GPT-4?** Structured output, consistent reasoning, and excellent at following complex prompts for diagnosis.

**Why Qdrant?** Free cloud tier, fast similarity search, and clean Python SDK. Perfect for storing incident embeddings.

**Why FastAPI?** Async support, automatic OpenAPI docs, Pydantic validation. Pairs perfectly with SQLAlchemy for the ORM layer.

**Why separate agents vs monolith?** Each agent has its own concerns, timer, and failure domain. If the Prediction Agent crashes, incidents still get diagnosed and fixed.

## Challenges

1. **Python 3.12 + passlib**: bcrypt's passlib wrapper has a bug on 3.12. Switched to direct bcrypt usage.

2. **UUID serialization**: SQLAlchemy returns UUID objects, Pydantic expects strings. Added field validators for automatic conversion.

3. **LLM fallbacks**: Claude API can be slow or unavailable. Every LLM-dependent feature has a template fallback that works without the API.

4. **Testing real integrations**: Tests need to work with or without real API keys. Used conditional assertions that accept both None (no key) and valid responses (key present).

## Results

- **20,000+ lines** of code across 200+ files
- **88 automated tests** — all passing
- **6 AI agents** in a coordinated pipeline
- **50+ API endpoints** with auth, caching, rate limiting
- **5 frontend pages** with real-time updates
- Sub-5-minute **mean time to resolution** for auto-remediated incidents

## Try It

The project is open source: [GitHub link]

```bash
docker compose up -d
cd backend && python src/main.py
cd frontend && npm run dev
```

The system will start monitoring, and you can trigger demo scenarios to see the full pipeline in action.
