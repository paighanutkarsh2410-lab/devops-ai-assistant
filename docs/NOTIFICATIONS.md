# Communication Agent & Notifications

The 6th agent in the pipeline. Manages all notification delivery across Slack, email, and in-app channels with smart routing, anti-spam, and user preferences.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                Communication Agent                   │
│               (runs every 300s)                      │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Event Router                                       │
│  ├─ Severity-based channel selection                │
│  ├─ User preference filtering                       │
│  ├─ Anti-spam (dedup, rate limit, quiet hours)      │
│  └─ Delivery tracking                              │
│                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│  │  Slack   │  │  Email   │  │  Digest  │         │
│  │ Notifier │  │ Notifier │  │  Buffer  │         │
│  └──────────┘  └──────────┘  └──────────┘         │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## Pipeline Position

```
Monitor → Diagnose → Remediate → Learn → Predict → Communicate
  30s       60s        90s       120s     3600s       300s
```

## Smart Routing

| Severity | Channels |
|----------|----------|
| Critical | Slack + Email |
| High | Slack + Email |
| Medium | Slack only |
| Low | Daily digest |
| Predictive | Email weekly summary |
| Approval | Slack (interactive buttons) |

## Slack Integration

### Message Types
- **Incident notifications** — Rich blocks with severity color, service, metrics, View/Acknowledge buttons
- **Remediation updates** — Thread replies showing status, action taken, before/after metrics
- **Approval requests** — Interactive Approve/Reject buttons with auto-timeout
- **Daily summary** — Yesterday's incidents, auto-resolved count, health score
- **Predictive alerts** — Forecast details, time until issue, recommended actions

### Setup
1. Create a Slack app at https://api.slack.com/apps
2. Add Bot Token Scopes: `chat:write`, `chat:write.public`
3. Install to workspace
4. Add to `.env`:
   ```
   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
   SLACK_BOT_TOKEN=xoxb-...
   SLACK_CHANNEL=#devops-alerts
   ```

## Email Integration

Uses Resend API (100 free emails/day).

### Templates
- **Incident email** — Full HTML with severity header, details table, metrics, dashboard link
- **Critical alert** — Brief, urgent red banner, SMS-like brevity
- **Weekly digest** — Stats cards, top incidents, insights, trends

### Setup
1. Sign up at https://resend.com
2. Add to `.env`:
   ```
   RESEND_API_KEY=re_...
   ```

## Anti-Spam Features

| Feature | Description |
|---------|-------------|
| Duplicate suppression | Same event won't notify twice within 5 minutes |
| Rate limiting | Slack: 5s between messages, Email: 60s |
| Quiet hours | 11 PM – 7 AM (critical still goes through) |
| Digest buffering | Low severity collected and sent in daily summary |

## Natural Language Chat

### Endpoint: `POST /chat/query`

Users can ask questions in plain English:
- "System status?" → Current health, open incidents, metrics
- "Show recent incidents" → Query database, list incidents
- "Why is the API slow?" → Fetch diagnostics, metrics, get AI analysis
- "Any predictions?" → Active predictive alerts
- "Cost forecast" → Monthly cost projections

Uses Claude Haiku for conversational responses. Falls back to templates when LLM unavailable.

### Suggested Queries: `GET /chat/suggestions`

Returns common questions as quick-action chips.

## Report Generation

### Types
| Report | Endpoint | Trigger |
|--------|----------|---------|
| Post-mortem | `GET /reports/incident/{id}/postmortem` | After critical incidents |
| Weekly health | `GET /reports/weekly` | Every Monday |
| Monthly trends | `GET /reports/monthly` | 1st of month |
| Executive summary | `GET /reports/executive` | On demand |

### Post-mortem includes:
- What happened, timeline, root cause, impact, resolution, lessons learned, action items

### Executive summary includes:
- Non-technical language, business impact, cost savings, reliability stats

## Notification Preferences

### User Settings
- Enable/disable per channel (Slack, email)
- Severity threshold (only notify at this level and above)
- Service subscriptions (specific services only)
- Quiet hours (start/end hour)
- Digest frequency (daily/weekly)

### On-Call Schedules
- Per-day-of-week schedules
- Start/end hours
- Auto-routing to on-call person

### API
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/preferences/notifications` | Get preferences |
| PUT | `/preferences/notifications` | Update preferences |
| POST | `/preferences/notifications/test` | Send test notification |
| GET | `/preferences/oncall` | Get on-call schedule |
| POST | `/preferences/oncall` | Set on-call schedule |

## Frontend Pages

- `/chat` — Full chat interface with AI assistant
- `/notifications` — Notification inbox with filters
- `/settings/notifications` — Preference toggles, service subscriptions, quiet hours

## Database Models

### NotificationPreference
User notification settings per channel.

### OnCallSchedule
Who's on-call when, for automatic routing.

### NotificationLog
Tracks all notifications sent — event type, channel, status, read/unread.
