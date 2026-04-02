# Remediation Agent

The Remediation Agent automatically fixes infrastructure issues using safe, audited actions with human-in-the-loop approval for high-risk operations.

## Architecture

```
Diagnosis Complete
    │
    ▼
┌──────────────────────────┐
│   Remediation Agent      │
│                          │
│  1. Load diagnosis       │
│  2. Select action        │──► Action Library (8 actions)
│  3. Safety checks        │──► Safety Rules + Approval
│  4. Execute action       │──► Docker / Kubernetes
│  5. Monitor impact       │──► Before/After metrics
│  6. Verify & update      │──► Success score 0-100
└──────────────────────────┘
```

## Pipeline

1. **Load Diagnosis** — Fetches incident with root cause from Diagnostic Agent
2. **Select Action** — Maps diagnosis keywords to remediation actions
3. **Safety Checks** — Validates against safety rules, checks approval requirements
4. **Execute** — Runs action through SafeExecutionFramework with checkpoint
5. **Monitor Impact** — Compares before/after metrics, auto-rollback if score < -20
6. **Verify & Update** — Runs verification checks, updates incident status

## Supported Actions

| Action | Risk | Description |
|---|---|---|
| restart_service | LOW | Restart a container/service |
| clear_cache | LOW | Flush Redis cache |
| adjust_rate_limit | LOW | Modify API rate limits |
| scale_service | MEDIUM | Scale replicas up/down |
| rollback_deployment | MEDIUM | Roll back to previous version |
| increase_resources | MEDIUM | Increase CPU/memory limits |
| kill_process | HIGH | Kill stuck/zombie processes |

## Safety Framework

- **Circuit breaker**: Stops after 3 consecutive failures
- **Rate limiting**: Max 3 restarts per service per hour
- **Approval workflow**: Required for HIGH risk actions and critical services
- **Dry-run mode**: Test actions without executing
- **Auto-rollback**: Triggered when impact score drops below -20
- **Checkpoints**: State snapshots before every action
- **Blackout windows**: Configurable no-touch periods

## Running

```bash
# Full pipeline (all 3 agents)
cd agents
python src/main.py

# Dry-run mode (no real actions)
python src/main.py --dry-run

# Without auto-remediation
python src/main.py --no-remediation
```

## Configuration

See `agents/config/remediation.yaml` for all options including:
- Allowed risk levels for auto-execution
- Services excluded from auto-remediation
- Approval requirements
- Blackout windows
