# User Guide

## Getting Started

1. **Sign up** at the login page with email and password
2. You'll land on the **Dashboard** — your central hub

## Dashboard

The dashboard shows:
- **Stats cards** — Total incidents, open, resolved, auto-resolved counts
- **Incident list** — Click any incident for details (diagnosis, timeline, remediation)
- **Live Metrics** — Real-time service metrics from Prometheus
- **Remediations** — Audit log of all automated actions

## Navigation

| Page | Purpose |
|------|---------|
| Dashboard | Main overview and incident management |
| Predictions | Forecasted issues, capacity planning, cost projections |
| Learning | Pattern recognition, trending issues, recommendation insights |
| Chat | Natural language interface — ask anything about your system |
| Notifications | Inbox of all alerts and notifications |
| System Health | Infrastructure and agent pipeline status |
| Settings | Notification preferences, quiet hours, service subscriptions |

## Understanding Alerts

**Severity levels:**
- **Critical** (red) — Immediate attention required, Slack + email sent
- **High** (orange) — Urgent but not outage-level, Slack + email sent
- **Medium** (yellow) — Needs investigation, Slack notification
- **Low** (green) — Informational, included in daily digest

## Predictions

The Prediction Agent analyzes trends to warn you before issues happen:
- **Predictive Alerts** — "Disk will fill in 12 days" with prevention actions
- **Capacity Plans** — When you'll need to scale, with recommendations
- **Cost Forecasts** — Monthly projections and optimization opportunities

## Chat Interface

Ask questions in natural language:
- "What's the system status?"
- "Show recent incidents"
- "Why is the API slow?"
- "Any predictions?"
- "Cost forecast for this month"

## Approval Workflow

High-risk remediation actions require human approval:
1. Agent proposes action → appears in Slack with Approve/Reject buttons
2. You review the action details and risk level
3. Click **Approve** or **Reject**
4. If no response within 30 minutes → auto-expires

## Reports

Available at `/reports`:
- **Post-mortem** — Auto-generated after critical incidents
- **Weekly Health** — Monday summary of past week
- **Monthly Trends** — Month-over-month comparison
- **Executive Summary** — Non-technical overview with cost savings
