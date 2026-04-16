#!/bin/bash
# Database backup script — run daily via cron
# Crontab: 0 2 * * * /opt/devops-ai/deployment/scripts/backup.sh

set -euo pipefail

BACKUP_DIR="/opt/devops-ai/deployment/production/backups"
DB_CONTAINER="devops-postgres"
DB_USER="${DB_USER:-devops_user}"
DB_NAME="${DB_NAME:-devops_ai}"
RETENTION_DAYS=7
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/backup_${TIMESTAMP}.sql.gz"

echo "[$(date)] Starting database backup..."

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Dump and compress
docker exec "$DB_CONTAINER" pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_FILE"

# Verify backup
if [ -s "$BACKUP_FILE" ]; then
    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "[$(date)] Backup successful: $BACKUP_FILE ($SIZE)"
else
    echo "[$(date)] ERROR: Backup file is empty!"
    rm -f "$BACKUP_FILE"
    exit 1
fi

# Clean old backups
find "$BACKUP_DIR" -name "backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete
echo "[$(date)] Cleaned backups older than $RETENTION_DAYS days"

# Count remaining backups
COUNT=$(find "$BACKUP_DIR" -name "backup_*.sql.gz" | wc -l)
echo "[$(date)] Total backups: $COUNT"

echo "[$(date)] Backup complete!"
