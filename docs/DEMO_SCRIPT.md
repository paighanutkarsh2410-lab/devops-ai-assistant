# Demo Video Script

**Duration**: 8-10 minutes
**Format**: Screen recording with voiceover

---

## 0:00-0:30 — Introduction

> "I built an AI-powered DevOps assistant that monitors infrastructure, detects problems, diagnoses root causes, and fixes them automatically — all with minimal human intervention."
>
> "This project uses 6 autonomous AI agents working in a pipeline, Claude API for intelligent analysis, and a full-stack dashboard for real-time monitoring."

---

## 0:30-2:00 — System Architecture

*Show architecture diagram from docs/ARCHITECTURE.md*

> "The system has three main layers:"
>
> "**Frontend** — A Next.js dashboard showing incidents, metrics, predictions, and a natural language chat interface."
>
> "**Backend** — FastAPI server handling authentication, data storage, and API endpoints. It's backed by PostgreSQL, Redis, and Prometheus."
>
> "**AI Agents** — Six agents running in a pipeline:"
> - "The **Monitor Agent** checks Prometheus every 30 seconds for anomalies using z-score and moving average algorithms"
> - "The **Diagnostic Agent** uses Claude API to analyze root causes and correlate with deployments and past incidents"
> - "The **Remediation Agent** executes fixes — restarts, scaling, rollbacks — with safety checkpoints and approval workflow for high-risk actions"
> - "The **Learning Agent** stores incident patterns in a vector database so the system gets smarter over time"
> - "The **Prediction Agent** forecasts issues before they happen using time-series analysis"
> - "The **Communication Agent** routes notifications to Slack and email based on severity"

---

## 2:00-4:00 — Live Demo: Incident Detection

*Show dashboard, then simulate a CPU spike*

> "Here's the dashboard. You can see current incidents, live metrics, and system health."
>
> "Let me simulate a CPU spike on the api-server..."

*Run demo command:*
```bash
cd agents && python examples/prediction_scenarios/disk_exhaustion.py
```

> "The Monitor Agent detects the anomaly within 30 seconds. An alert appears on the dashboard with severity level and affected service."
>
> "It's also sent to Slack in real-time with an interactive notification."

---

## 4:00-6:00 — Live Demo: AI Diagnosis & Remediation

> "Now the Diagnostic Agent kicks in. It queries Claude API with the incident context — metrics, recent deployments, similar past incidents."
>
> "You can see the diagnosis here — it identified the root cause with 92% confidence, correlated it with a deployment made 2 hours ago."

*Click incident → show diagnosis panel*

> "The Remediation Agent proposes a fix. For this medium-risk action, it executes automatically. For high-risk actions, it would send an approval request to Slack."
>
> "Watch the before and after metrics — CPU dropped from 95% back to normal. The incident is now auto-resolved."

---

## 6:00-7:30 — Predictions & Learning

*Navigate to Predictions page*

> "The Prediction Agent analyzes trends and warns you before issues happen. Here you can see it predicting disk exhaustion in 12 days and recommending preventive action."
>
> "The cost forecaster shows monthly projections with optimization suggestions."

*Navigate to Learning page*

> "The Learning Agent has identified 3 trending patterns. It uses vector similarity search to match new incidents with historical data, improving diagnosis accuracy over time."

---

## 7:30-8:30 — Chat & Notifications

*Navigate to Chat page*

> "You can ask questions in natural language: 'What's the system status?' 'Why is the API slow?' 'Any predictions?'"
>
> "It queries the database, runs analysis, and responds conversationally."

*Show Slack messages*

> "All critical notifications go to Slack with rich formatting, interactive buttons, and daily summaries."

---

## 8:30-10:00 — Conclusion

> "To recap: this is a production-ready DevOps assistant with:"
> - "6 AI agents in an automated pipeline"
> - "Real-time monitoring with Prometheus"
> - "Claude API for intelligent analysis"
> - "Safety-first remediation with approval workflow"
> - "Vector database for pattern learning"
> - "Time-series forecasting for predictions"
> - "Multi-channel notifications via Slack and email"
> - "Full-stack dashboard with Next.js"
>
> "Built over 10 days with ~20,000 lines of code across 200+ files."
>
> "The code is open source — link in the description. Thanks for watching!"

---

## Recording Tips

- Resolution: 1920x1080
- Browser: Chrome (dark dev tools hidden)
- Terminal: Clean, large font (16px+)
- Zoom in on important UI elements
- Pre-stage all demo data before recording
- Have backend + agents running before recording starts
