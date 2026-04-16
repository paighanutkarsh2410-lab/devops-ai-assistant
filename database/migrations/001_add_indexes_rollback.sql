-- Rollback Migration 001: Remove performance indexes
BEGIN;

DROP INDEX IF EXISTS idx_incidents_user_status;
DROP INDEX IF EXISTS idx_incidents_service_time;
DROP INDEX IF EXISTS idx_incidents_severity_time;
DROP INDEX IF EXISTS idx_metrics_service_metric_time;
DROP INDEX IF EXISTS idx_metrics_time_value;
DROP INDEX IF EXISTS idx_alerts_user_resolved;
DROP INDEX IF EXISTS idx_logs_service_level_time;
DROP INDEX IF EXISTS idx_notif_logs_event_time;
DROP INDEX IF EXISTS idx_notif_logs_status;
DROP INDEX IF EXISTS idx_action_logs_incident;
DROP INDEX IF EXISTS idx_pred_alerts_severity;
DROP INDEX IF EXISTS idx_pred_alerts_prevented;

COMMIT;
