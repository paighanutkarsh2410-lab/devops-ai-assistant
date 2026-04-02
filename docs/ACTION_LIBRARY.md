# Action Library

All available remediation actions with their risk levels, behavior, and configuration.

## Action Interface

Every action implements:
- `validate(context)` — Pre-execution checks
- `execute(context)` — Perform the action
- `rollback(context)` — Undo the action
- `verify(context)` — Confirm success

## Actions

### restart_service (LOW risk)
Restarts a Docker container or Kubernetes pod. Most common remediation for transient issues like memory leaks, stuck processes, or cache corruption.

- **Rollback**: None needed (restart is idempotent)
- **Rate limit**: Max 3 per hour per service

### scale_service (MEDIUM risk)
Scales service replicas up or down. Used for handling load spikes or resource pressure.

- **Limits**: Max 10 replicas
- **Rollback**: Scale back to original count
- **Supports**: Docker Compose and Kubernetes deployments

### rollback_deployment (MEDIUM risk)
Rolls back to the previous deployment version. Used when a new deployment causes errors.

- **Requires approval**: Yes (by default)
- **Rollback**: Redeploy the rolled-back version
- **Supports**: Kubernetes rollback

### clear_cache (LOW risk)
Flushes Redis cache, either specific keys (by pattern) or all keys.

- **Rollback**: Cache rebuilds naturally
- **Options**: `cache_pattern` for selective flush

### increase_resources (MEDIUM risk)
Increases CPU or memory limits for a service.

- **Requires approval**: Yes
- **Limits**: Max 100% increase
- **Rollback**: Revert to original limits

### kill_process (HIGH risk)
Kills stuck or zombie processes inside a container.

- **Requires approval**: Yes (always)
- **Target**: By process name or PID
- **Rollback**: Restart service if needed

### adjust_rate_limit (LOW risk)
Temporarily adjusts API rate limits via Redis.

- **Duration**: Configurable (default 30 minutes)
- **Rollback**: Restores original limit or auto-reverts on TTL expiry

## Adding Custom Actions

1. Create a class extending `RemediationAction` in `agents/src/actions/`
2. Implement `validate()`, `execute()`, `rollback()`
3. Register in `agents/src/actions/__init__.py`
