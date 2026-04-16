-- Migration 001: Add performance indexes
-- Run: psql -U devops_user -d devops_ai -f 001_add_indexes.sql
-- Rollback: psql -U devops_user -d devops_ai -f 001_add_indexes_rollback.sql

BEGIN;

-- Incidents
CREATE INDEX IF NOT EXISTS idx_incidents_user_status ON incidents(user_id, status);
CREATE INDEX IF NOT EXISTS idx_incidents_service_time ON incidents(service_name, detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_incidents_severity_time ON incidents(severity, detected_at DESC);

-- Metrics
CREATE INDEX IF NOT EXISTS idx_metrics_service_metric_time ON metrics(service_name, metric_name, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_metrics_time_value ON metrics(timestamp DESC, value);

-- Alerts
CREATE INDEX IF NOT EXISTS idx_alerts_user_resolved ON alerts(user_id, resolved, triggered_at DESC);

-- Logs
CREATE INDEX IF NOT EXISTS idx_logs_service_level_time ON log_entries(service_name, level, timestamp DESC);

-- Notification logs
CREATE INDEX IF NOT EXISTS idx_notif_logs_event_time ON notification_logs(event_type, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_notif_logs_status ON notification_logs(status, created_at DESC);

-- Action logs
CREATE INDEX IF NOT EXISTS idx_action_logs_incident ON action_logs(incident_id, executed_at DESC);

-- Predictive alerts
CREATE INDEX IF NOT EXISTS idx_pred_alerts_severity ON predictive_alerts(severity, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_pred_alerts_prevented ON predictive_alerts(prevented, created_at DESC);

COMMIT;
