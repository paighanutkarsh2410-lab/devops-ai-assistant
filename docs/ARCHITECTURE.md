# Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Next.js)                       │
│  Dashboard │ Chat │ Predictions │ Learning │ Notifications   │
└──────────────────────────┬──────────────────────────────────┘
                           │ REST + WebSocket
┌──────────────────────────▼──────────────────────────────────┐
│                   Backend (FastAPI)                           │
│  Auth │ Incidents │ Metrics │ Alerts │ Reports │ Preferences │
│  ─── Middleware: Cache │ Rate Limit │ Security │ GZip ───     │
└──┬──────────┬─────────────┬──────────────┬──────────────────┘
   │          │             │              │
   ▼          ▼             ▼              ▼
PostgreSQL  Redis      Prometheus      Claude API
 (data)    (cache)    (metrics)        (AI brain)
                           │
                    Grafana (viz)
```

## Agent Pipeline

Six autonomous agents run in a coordinated pipeline:

```
Monitor (30s) → Diagnose (60s) → Remediate (90s) → Learn (120s) → Predict (3600s) → Communicate (300s)
```

| Agent | Purpose | Key Tech |
|-------|---------|----------|
| **Monitor** | Anomaly detection via z-score, moving average, thresholds | Prometheus, WebSocket |
| **Diagnostic** | AI-powered root cause analysis, correlation engine | Claude API, TF-IDF |
| **Remediation** | Safe auto-fix with approval workflow, rollback | Docker, K8s, Circuit breaker |
| **Learning** | Pattern recognition, feedback loops, recommendations | Qdrant, Sentence-Transformers |
| **Prediction** | Time-series forecasting, capacity planning | Prophet, Linear regression |
| **Communication** | Smart notification routing, NL chat, reports | Slack, Resend, Claude Haiku |

## Data Flow

1. **Detection**: Monitor agent polls Prometheus → detects anomaly → creates incident
2. **Diagnosis**: Diagnostic agent picks up incident → correlates with deployments, metrics, logs → Claude AI analysis
3. **Remediation**: Remediation agent selects strategy → safety checks → execute (with approval if high risk) → verify
4. **Learning**: Learning agent records outcome → updates patterns → adjusts thresholds via feedback loop
5. **Prediction**: Prediction agent forecasts metrics → detects trends → generates predictive alerts
6. **Communication**: Communication agent routes notifications → Slack/email based on severity → anti-spam filtering

## Database Schema

- **Users** → own all data (multi-tenant)
- **Incidents** → core entity, linked to alerts, actions, diagnostics
- **Metrics** → time-series from Prometheus (90-day retention)
- **Alerts** → triggered by anomalies, can be acknowledged/resolved
- **Log Entries** → service logs (30-day retention)
- **Deployments** → tracked for correlation with incidents
- **Action Logs** → audit trail of all remediation actions
- **Patterns** → learned from historical incidents
- **Predictive Alerts** → forecasted issues with prevention tracking
- **Notification Logs** → delivery tracking across channels

## Security Layers

1. **Transport**: HTTPS/TLS everywhere
2. **Auth**: JWT tokens (7-day expiry), bcrypt password hashing
3. **Input**: Validation, sanitization, SQL injection prevention
4. **Headers**: CSP, HSTS, X-Frame-Options, X-Content-Type-Options
5. **Rate Limiting**: Per-IP (200 req/hr), per-user tiers
6. **Encryption**: Fernet for sensitive fields at rest
7. **Audit**: All auth events and privileged actions logged

## Performance Optimizations

- **Database**: Connection pooling (5-20 connections), composite indexes, data archival
- **Caching**: Redis-backed response cache (5min metrics, 1hr predictions)
- **API**: GZip compression (>1KB), rate limiting, pagination (default 50)
- **Frontend**: Code splitting, skeleton loaders, error boundaries
