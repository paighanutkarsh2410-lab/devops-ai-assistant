# Runbooks

Operational procedures for when automated remediation needs human intervention.

## When Auto-Remediation Fails

If the agent marks an incident as `needs_human`:

1. Check the audit log at `/audit` for what was attempted
2. Review the impact score — negative means the action made things worse
3. Check if rollback was performed automatically
4. Apply manual fix based on the diagnosis

## Emergency: Disable Auto-Remediation

### Option 1: CLI flag
```bash
python src/main.py --no-remediation
```

### Option 2: Config file
Edit `agents/config/remediation.yaml`:
```yaml
auto_remediation_enabled: false
```

### Option 3: Exclude specific service
```yaml
excluded_services:
  - payment-api
  - database-primary
  - auth-service
```

## Manual Rollback Procedures

### Container Restart Issues
```bash
docker restart <container-name>
docker logs <container-name> --tail 50
```

### Bad Deployment
```bash
# Docker
docker-compose up -d --force-recreate <service>

# Kubernetes
kubectl rollout undo deployment/<name>
kubectl rollout status deployment/<name>
```

### Database Connection Issues
1. Check connection pool: `SELECT count(*) FROM pg_stat_activity`
2. Kill idle connections if needed
3. Restart the backend service

### Redis Cache Issues
```bash
redis-cli FLUSHDB  # Clear current database
redis-cli INFO memory  # Check memory usage
```

## Monitoring After Manual Fix

1. Watch metrics for 5 minutes after any fix
2. Check error rates are declining
3. Verify dependent services are healthy
4. Update the incident status to `resolved`

## Escalation Path

1. **Auto-remediation** tries first (LOW/MEDIUM risk)
2. **Approval required** for HIGH risk actions
3. **needs_human** status if auto-fix fails
4. Manual intervention by on-call engineer
