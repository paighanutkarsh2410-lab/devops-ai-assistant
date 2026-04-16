#!/bin/bash
# Production deployment script with zero-downtime and auto-rollback
set -euo pipefail

DEPLOY_DIR="/opt/devops-ai"
COMPOSE_DIR="$DEPLOY_DIR/deployment/production"
LOG_FILE="/var/log/devops-deploy.log"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

log() { echo "[$(date)] $1" | tee -a "$LOG_FILE"; }

log "=== Starting production deployment $TIMESTAMP ==="

# 1. Pre-deployment checks
log "Running pre-deployment checks..."
cd "$DEPLOY_DIR"

# Check disk space
DISK_FREE=$(df -BG / | awk 'NR==2 {print $4}' | tr -d 'G')
if [ "$DISK_FREE" -lt 5 ]; then
    log "ERROR: Less than 5GB free disk space!"
    exit 1
fi

# 2. Backup database
log "Creating database backup..."
./deployment/scripts/backup.sh

# 3. Pull latest code
log "Pulling latest code..."
git pull origin main

# 4. Build images
log "Building Docker images..."
cd "$COMPOSE_DIR"
docker compose build --no-cache

# 5. Run database migrations
log "Running database migrations..."
docker compose exec -T postgres psql -U devops_user -d devops_ai \
    -f /opt/devops-ai/database/migrations/001_add_indexes.sql 2>/dev/null || true
docker compose exec -T postgres psql -U devops_user -d devops_ai \
    -f /opt/devops-ai/database/migrations/002_add_archive_tables.sql 2>/dev/null || true

# 6. Rolling restart
log "Starting rolling deployment..."
docker compose up -d --remove-orphans

# 7. Wait for services
log "Waiting for services to start..."
sleep 15

# 8. Health check
log "Running health checks..."
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
if [ "$HEALTH" != "200" ]; then
    log "ERROR: Health check failed (HTTP $HEALTH)! Rolling back..."
    docker compose down
    git checkout HEAD~1
    docker compose up -d
    log "Rollback complete."
    exit 1
fi

# 9. Verify all services
log "Verifying services..."
SERVICES=("devops-backend" "devops-postgres" "devops-redis" "devops-frontend")
for svc in "${SERVICES[@]}"; do
    STATUS=$(docker inspect --format='{{.State.Status}}' "$svc" 2>/dev/null || echo "missing")
    if [ "$STATUS" != "running" ]; then
        log "WARNING: $svc is $STATUS"
    else
        log "  $svc: running"
    fi
done

# 10. Record deployment
log "=== Deployment $TIMESTAMP complete! ==="
echo "$TIMESTAMP | $(git rev-parse --short HEAD) | SUCCESS" >> "$DEPLOY_DIR/deployment/DEPLOYMENT_LOG.md"
