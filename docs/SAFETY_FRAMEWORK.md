# Safety Framework

Safety is the foundation of automated remediation. The framework ensures that automated actions never make things worse.

## Philosophy

1. **Do no harm** — Every action must be validated before execution
2. **Always recoverable** — Checkpoints enable rollback of any action
3. **Human override** — Critical decisions require human approval
4. **Transparent** — Every action is logged in the audit trail
5. **Self-limiting** — Circuit breaker stops runaway automation

## Components

### SafeExecutionFramework

The central execution engine that wraps every action with safety checks:

```
Pre-validation → Checkpoint → Execute → Monitor → Auto-rollback if needed
```

### SafetyRules

Enforces policies:
- **Rate limiting**: Max restarts per service per hour
- **Risk filtering**: Only allowed risk levels auto-execute
- **Service exclusion**: Critical services can be protected
- **Blackout windows**: No actions during configured time windows

### CheckpointManager

Creates JSON snapshots of service state before each action:
- Metrics snapshot
- Container state
- Configuration
- Replica count
- Version info

Checkpoints are stored in `agents/data/checkpoints/` and auto-cleaned after 24 hours.

## Approval Workflow

For high-risk actions:

1. Agent creates approval request via `/approvals/` API
2. Request appears in frontend dashboard
3. Human approves or rejects
4. Agent polls for response (5-minute timeout in agent, 30-minute expiry)
5. Expired requests are auto-rejected

Actions requiring approval:
- `kill_process` (HIGH risk)
- `rollback_deployment` (MEDIUM but impactful)
- `increase_resources` (MEDIUM but costly)
- Any action on `payment-api` or `database-primary`

## Impact Monitoring

After every action, the framework:
1. Compares baseline metrics to current metrics
2. Calculates weighted impact score (-100 to +100)
3. Triggers auto-rollback if score < -20

Metric weights:
- Error rate: 3x (most critical)
- Response time: 2x
- CPU/Memory: 1x

## Circuit Breaker

After 3 consecutive failures:
- All actions are blocked
- Manual reset required (`framework.reset_circuit_breaker()`)
- Prevents cascading automated failures
