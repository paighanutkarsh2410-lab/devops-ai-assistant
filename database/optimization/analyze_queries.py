"""
Database Performance Analyzer: Identifies slow queries, missing indexes,
and optimization opportunities for PostgreSQL.
"""
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


@dataclass
class QueryAnalysis:
    query: str
    calls: int
    mean_time_ms: float
    total_time_ms: float
    rows_per_call: float
    cache_hit_ratio: float
    suggestion: str = ""
    severity: str = "info"  # info, warning, critical


@dataclass
class IndexRecommendation:
    table: str
    columns: List[str]
    index_type: str  # btree, hash, gin, gist
    reason: str
    estimated_improvement: str
    create_sql: str


class DatabaseAnalyzer:
    """
    Analyzes PostgreSQL performance and recommends optimizations.
    """

    # Queries for performance analysis
    SLOW_QUERIES_SQL = """
    SELECT query, calls, mean_exec_time, total_exec_time, rows
    FROM pg_stat_statements
    ORDER BY mean_exec_time DESC
    LIMIT 20;
    """

    CACHE_HIT_RATIO_SQL = """
    SELECT
        schemaname, relname,
        heap_blks_read, heap_blks_hit,
        CASE WHEN heap_blks_read + heap_blks_hit > 0
            THEN round(heap_blks_hit::numeric / (heap_blks_read + heap_blks_hit), 4)
            ELSE 1
        END AS cache_hit_ratio
    FROM pg_statio_user_tables
    ORDER BY heap_blks_read DESC
    LIMIT 20;
    """

    ACTIVE_QUERIES_SQL = """
    SELECT pid, age(clock_timestamp(), query_start) AS duration,
           usename, query, state
    FROM pg_stat_activity
    WHERE state != 'idle'
    ORDER BY query_start;
    """

    LOCK_MONITORING_SQL = """
    SELECT blocked_locks.pid AS blocked_pid,
           blocked_activity.usename AS blocked_user,
           blocking_locks.pid AS blocking_pid,
           blocking_activity.usename AS blocking_user,
           blocked_activity.query AS blocked_query
    FROM pg_catalog.pg_locks blocked_locks
    JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
    JOIN pg_catalog.pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype
        AND blocking_locks.relation = blocked_locks.relation
    JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
    WHERE NOT blocked_locks.granted;
    """

    TABLE_SIZES_SQL = """
    SELECT relname AS table_name,
           pg_size_pretty(pg_total_relation_size(relid)) AS total_size,
           pg_size_pretty(pg_relation_size(relid)) AS data_size,
           pg_size_pretty(pg_total_relation_size(relid) - pg_relation_size(relid)) AS index_size,
           n_live_tup AS row_count
    FROM pg_stat_user_tables
    ORDER BY pg_total_relation_size(relid) DESC;
    """

    UNUSED_INDEXES_SQL = """
    SELECT schemaname, relname AS table, indexrelname AS index,
           idx_scan AS scans, pg_size_pretty(pg_relation_size(i.indexrelid)) AS size
    FROM pg_stat_user_indexes i
    JOIN pg_index USING (indexrelid)
    WHERE idx_scan < 50 AND NOT indisunique
    ORDER BY pg_relation_size(i.indexrelid) DESC;
    """

    def __init__(self):
        self._analyses: List[QueryAnalysis] = []
        self._index_recommendations: List[IndexRecommendation] = []

    def run_full_analysis(self) -> Dict[str, Any]:
        """Run comprehensive database analysis (simulated for demo)."""
        started = datetime.now(timezone.utc)

        # Simulate query analysis
        self._analyses = self._simulate_slow_queries()
        self._index_recommendations = self._generate_index_recommendations()

        return {
            "analyzed_at": started.isoformat(),
            "slow_queries": [
                {
                    "query": qa.query[:120] + "..." if len(qa.query) > 120 else qa.query,
                    "calls": qa.calls,
                    "mean_time_ms": round(qa.mean_time_ms, 2),
                    "total_time_ms": round(qa.total_time_ms, 2),
                    "rows_per_call": round(qa.rows_per_call, 1),
                    "cache_hit_ratio": qa.cache_hit_ratio,
                    "suggestion": qa.suggestion,
                    "severity": qa.severity,
                }
                for qa in self._analyses
            ],
            "index_recommendations": [
                {
                    "table": ir.table,
                    "columns": ir.columns,
                    "index_type": ir.index_type,
                    "reason": ir.reason,
                    "estimated_improvement": ir.estimated_improvement,
                    "create_sql": ir.create_sql,
                }
                for ir in self._index_recommendations
            ],
            "connection_pool": {
                "pool_size": 20,
                "max_overflow": 40,
                "pool_pre_ping": True,
                "pool_recycle_seconds": 3600,
                "active_connections": 12,
                "idle_connections": 8,
                "overflow_connections": 0,
            },
            "table_stats": self._simulate_table_stats(),
            "recommendations": self._generate_recommendations(),
        }

    def _simulate_slow_queries(self) -> List[QueryAnalysis]:
        """Simulate slow query analysis results."""
        return [
            QueryAnalysis(
                query="SELECT * FROM incidents WHERE user_id = $1 AND status = $2 ORDER BY created_at DESC",
                calls=15420, mean_time_ms=45.2, total_time_ms=697104.0,
                rows_per_call=8.3, cache_hit_ratio=0.94,
                suggestion="Add composite index on (user_id, status, created_at DESC)",
                severity="warning",
            ),
            QueryAnalysis(
                query="SELECT m.*, s.name FROM metrics m JOIN services s ON m.service_id = s.id WHERE m.timestamp > $1",
                calls=8900, mean_time_ms=78.5, total_time_ms=698650.0,
                rows_per_call=250.0, cache_hit_ratio=0.87,
                suggestion="Add index on metrics(timestamp). Consider partitioning by month.",
                severity="warning",
            ),
            QueryAnalysis(
                query="SELECT COUNT(*) FROM alerts WHERE user_id = $1 AND acknowledged = false",
                calls=42000, mean_time_ms=12.1, total_time_ms=508200.0,
                rows_per_call=1.0, cache_hit_ratio=0.98,
                suggestion="Index on (user_id, acknowledged) covers this query well.",
                severity="info",
            ),
            QueryAnalysis(
                query="SELECT * FROM action_logs WHERE incident_id = $1 ORDER BY executed_at DESC LIMIT 50",
                calls=6200, mean_time_ms=35.8, total_time_ms=221960.0,
                rows_per_call=12.5, cache_hit_ratio=0.91,
                suggestion="Add index on action_logs(incident_id, executed_at DESC)",
                severity="info",
            ),
            QueryAnalysis(
                query="UPDATE incidents SET status = $1, resolved_at = $2 WHERE id = $3",
                calls=890, mean_time_ms=8.5, total_time_ms=7565.0,
                rows_per_call=1.0, cache_hit_ratio=0.99,
                suggestion="Primary key lookup — no optimization needed.",
                severity="info",
            ),
        ]

    def _generate_index_recommendations(self) -> List[IndexRecommendation]:
        """Generate index recommendations."""
        return [
            IndexRecommendation(
                table="incidents",
                columns=["user_id", "status", "created_at"],
                index_type="btree",
                reason="Covers common dashboard query pattern: user incidents filtered by status, ordered by date",
                estimated_improvement="40-60% reduction in query time",
                create_sql="CREATE INDEX CONCURRENTLY idx_incidents_user_status_created ON incidents(user_id, status, created_at DESC);",
            ),
            IndexRecommendation(
                table="metrics",
                columns=["service_name", "timestamp"],
                index_type="btree",
                reason="Covers time-range queries for service metrics",
                estimated_improvement="50-70% reduction for time-series queries",
                create_sql="CREATE INDEX CONCURRENTLY idx_metrics_service_time ON metrics(service_name, timestamp DESC);",
            ),
            IndexRecommendation(
                table="alerts",
                columns=["user_id", "acknowledged", "created_at"],
                index_type="btree",
                reason="Covers unacknowledged alert queries with date ordering",
                estimated_improvement="30-50% reduction in alert queries",
                create_sql="CREATE INDEX CONCURRENTLY idx_alerts_user_ack_created ON alerts(user_id, acknowledged, created_at DESC);",
            ),
            IndexRecommendation(
                table="action_logs",
                columns=["incident_id", "executed_at"],
                index_type="btree",
                reason="Covers action log lookups per incident",
                estimated_improvement="35-55% reduction for action log queries",
                create_sql="CREATE INDEX CONCURRENTLY idx_action_logs_incident_time ON action_logs(incident_id, executed_at DESC);",
            ),
        ]

    def _simulate_table_stats(self) -> List[Dict[str, Any]]:
        """Simulate table size stats."""
        return [
            {"table": "metrics", "total_size": "2.4 GB", "data_size": "1.8 GB", "index_size": "620 MB", "rows": 12500000},
            {"table": "incidents", "total_size": "180 MB", "data_size": "120 MB", "index_size": "60 MB", "rows": 45000},
            {"table": "alerts", "total_size": "95 MB", "data_size": "65 MB", "index_size": "30 MB", "rows": 128000},
            {"table": "action_logs", "total_size": "52 MB", "data_size": "38 MB", "index_size": "14 MB", "rows": 67000},
            {"table": "users", "total_size": "2 MB", "data_size": "1.5 MB", "index_size": "500 KB", "rows": 350},
        ]

    def _generate_recommendations(self) -> List[Dict[str, Any]]:
        """Generate overall recommendations."""
        return [
            {
                "category": "Indexing",
                "priority": "high",
                "recommendation": "Add 4 composite indexes to cover slow query patterns",
                "impact": "40-70% improvement on common queries",
            },
            {
                "category": "Partitioning",
                "priority": "medium",
                "recommendation": "Partition metrics table by month (2.4 GB and growing)",
                "impact": "Faster queries, easier archival, reduced vacuum time",
            },
            {
                "category": "Connection Pooling",
                "priority": "low",
                "recommendation": "Current pool (20+40 overflow) is adequate. Monitor under load.",
                "impact": "Prevents connection exhaustion under spike load",
            },
            {
                "category": "Vacuum",
                "priority": "medium",
                "recommendation": "Schedule VACUUM ANALYZE weekly for metrics and alerts tables",
                "impact": "Maintains query planner accuracy and reclaims dead tuples",
            },
            {
                "category": "Archival",
                "priority": "medium",
                "recommendation": "Archive metrics older than 90 days to cold storage",
                "impact": "Reduces active table size by ~60%, faster queries",
            },
        ]
