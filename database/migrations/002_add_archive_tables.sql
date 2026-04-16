-- Migration 002: Create archive tables for data retention
BEGIN;

CREATE TABLE IF NOT EXISTS archived_incidents (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    title VARCHAR NOT NULL,
    description TEXT,
    severity VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    service_name VARCHAR,
    root_cause VARCHAR,
    solution VARCHAR,
    detected_at TIMESTAMP,
    resolved_at TIMESTAMP,
    created_at TIMESTAMP,
    auto_resolved BOOLEAN DEFAULT FALSE,
    resolution_time_seconds INTEGER,
    extra_data JSONB,
    archived_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS archived_metrics (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    service_name VARCHAR NOT NULL,
    metric_name VARCHAR NOT NULL,
    value FLOAT NOT NULL,
    unit VARCHAR,
    timestamp TIMESTAMP NOT NULL,
    archived_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_archived_metrics_service_time ON archived_metrics(service_name, timestamp);

COMMIT;
