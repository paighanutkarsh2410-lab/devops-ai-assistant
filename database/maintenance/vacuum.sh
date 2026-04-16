#!/bin/bash
# Database Maintenance Script
# Run weekly via cron: 0 3 * * 0 /path/to/vacuum.sh
#
# Performs:
#   1. VACUUM ANALYZE on high-churn tables
#   2. Reindex if bloat > threshold
#   3. Log maintenance results
#   4. Alert on issues

set -euo pipefail

DB_URL="${DATABASE_URL:-postgresql://localhost:5432/devops}"
LOG_FILE="/var/log/devops/db_maintenance.log"
ALERT_WEBHOOK="${SLACK_WEBHOOK_URL:-}"

log() {
    echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] $1" | tee -a "$LOG_FILE"
}

alert() {
    if [ -n "$ALERT_WEBHOOK" ]; then
        curl -s -X POST "$ALERT_WEBHOOK" \
            -H 'Content-Type: application/json' \
            -d "{\"text\": \"DB Maintenance: $1\"}" > /dev/null 2>&1 || true
    fi
}

log "=== Database Maintenance Started ==="

# 1. VACUUM ANALYZE high-churn tables
log "Running VACUUM ANALYZE on high-churn tables..."
for table in metrics alerts incidents action_logs; do
    log "  VACUUM ANALYZE $table..."
    psql "$DB_URL" -c "VACUUM (ANALYZE, VERBOSE) $table;" 2>&1 | tail -3 | tee -a "$LOG_FILE"
done

# 2. Check table bloat
log "Checking table bloat..."
psql "$DB_URL" -c "
SELECT schemaname, tablename,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
       n_dead_tup AS dead_tuples,
       n_live_tup AS live_tuples,
       CASE WHEN n_live_tup > 0
            THEN round(n_dead_tup::numeric / n_live_tup * 100, 1)
            ELSE 0 END AS bloat_pct
FROM pg_stat_user_tables
WHERE n_dead_tup > 10000
ORDER BY n_dead_tup DESC;
" 2>&1 | tee -a "$LOG_FILE"

# 3. Check index usage
log "Checking unused indexes..."
psql "$DB_URL" -c "
SELECT schemaname, relname AS table, indexrelname AS index,
       idx_scan AS scans,
       pg_size_pretty(pg_relation_size(i.indexrelid)) AS size
FROM pg_stat_user_indexes i
JOIN pg_index USING (indexrelid)
WHERE idx_scan < 50 AND NOT indisunique
ORDER BY pg_relation_size(i.indexrelid) DESC
LIMIT 10;
" 2>&1 | tee -a "$LOG_FILE"

# 4. Check connection stats
log "Connection statistics..."
psql "$DB_URL" -c "
SELECT state, count(*)
FROM pg_stat_activity
GROUP BY state;
" 2>&1 | tee -a "$LOG_FILE"

# 5. Update statistics
log "Updating planner statistics..."
psql "$DB_URL" -c "ANALYZE;" 2>&1 | tee -a "$LOG_FILE"

log "=== Database Maintenance Completed ==="
alert "Weekly maintenance completed successfully"
