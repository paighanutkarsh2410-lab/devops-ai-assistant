#!/bin/bash
# Rollback to previous deployment
set -euo pipefail

DEPLOY_DIR="/opt/devops-ai"
COMPOSE_DIR="$DEPLOY_DIR/deployment/production"
BACKUP_DIR="$COMPOSE_DIR/backups"

echo "[$(date)] Starting rollback..."

cd "$DEPLOY_DIR"

# 1. Revert code
echo "[$(date)] Reverting to previous commit..."
git checkout HEAD~1

# 2. Find latest backup
LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/backup_*.sql.gz 2>/dev/null | head -1)
if [ -n "$LATEST_BACKUP" ]; then
    echo "[$(date)] Restoring database from: $LATEST_BACKUP"
    gunzip -c "$LATEST_BACKUP" | docker exec -i devops-postgres psql -U devops_user -d devops_ai
else
    echo "[$(date)] WARNING: No backup found, skipping DB restore"
fi

# 3. Rebuild and restart
echo "[$(date)] Rebuilding containers..."
cd "$COMPOSE_DIR"
docker compose build
docker compose up -d

# 4. Verify
sleep 10
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
if [ "$HEALTH" == "200" ]; then
    echo "[$(date)] Rollback successful!"
else
    echo "[$(date)] ERROR: Rollback health check failed!"
    exit 1
fi
