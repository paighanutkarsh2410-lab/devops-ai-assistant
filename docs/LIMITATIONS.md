# Known Limitations

## Current Limitations (v1.0)

### Architecture
- **Single-user focus** — No multi-tenancy or team features yet
- **Single-node deployment** — No horizontal scaling or load balancing
- **No high availability** — Single point of failure for each service

### AI & ML
- **Prediction accuracy ~75-80%** — Linear regression fallback when Prophet unavailable
- **Claude API dependency** — Diagnosis quality depends on API availability and cost
- **Cold start** — Learning agent needs incidents to build knowledge base
- **No custom training** — Uses pre-trained models, no fine-tuning on domain data

### Remediation
- **Limited action library** — 7 predefined actions (restart, scale, rollback, etc.)
- **Docker/K8s only** — No support for bare metal or cloud-native services
- **No complex workflows** — Single-step actions, no multi-step runbooks
- **Dry run by default** — Must explicitly enable auto-remediation

### Monitoring
- **Prometheus only** — No support for Datadog, CloudWatch, etc.
- **Simple anomaly detection** — Z-score and moving average, no advanced ML
- **No custom metrics** — Must configure Prometheus scrape targets manually

### Notifications
- **Slack + Email only** — No SMS, Teams, Discord, PagerDuty
- **No escalation policies** — Simple severity-based routing only
- **No on-call rotation** — Schema exists but not fully implemented

### Security
- **No MFA** — Single-factor authentication only
- **No SSO** — No SAML/OIDC support
- **Basic RBAC** — Admin/user only, no custom roles

### Frontend
- **Desktop-optimized** — Responsive but not mobile-first
- **No offline support** — Requires active internet connection
- **No i18n** — English only
