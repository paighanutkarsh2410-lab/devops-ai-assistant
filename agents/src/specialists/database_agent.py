"""
Database Specialist Agent: Slow queries, index recommendations,
connection pool analysis, deadlock detection, query plan analysis.
"""
import re
import logging
from typing import Dict, List
from .base_specialist import BaseSpecialist, SpecialistReport, Finding

logger = logging.getLogger(__name__)


class DatabaseSpecialistAgent(BaseSpecialist):
    AGENT_TYPE = "database"
    DOMAINS = ["database", "performance"]
    ACTIONS = ["diagnose", "investigate", "optimize"]

    # Thresholds
    SLOW_QUERY_MS = 500
    MAX_POOL_USAGE_PCT = 85
    HIGH_LOCK_WAIT_MS = 1000

    def __init__(self):
        super().__init__("database-specialist")

    def _perform_analysis(self, incident: dict, context: dict, report: SpecialistReport):
        service = incident.get("service_name", "unknown")
        root_cause = (incident.get("root_cause") or "").lower()
        description = (incident.get("description") or "").lower()
        text = f"{root_cause} {description}"

        if any(k in text for k in ("slow query", "query", "select", "latency")):
            self._detect_slow_queries(service, report)
        if any(k in text for k in ("connection", "pool", "max_connections")):
            self._analyze_connection_pool(service, report)
        if any(k in text for k in ("deadlock", "lock", "waiting")):
            self._detect_deadlocks(service, report)
        if any(k in text for k in ("index", "scan", "seq_scan")):
            self._recommend_indexes(service, report)

        # Always run general DB health
        self._check_db_health(service, report)

    def _detect_slow_queries(self, service: str, report: SpecialistReport):
        # Simulated slow query detection (in production: query pg_stat_statements)
        slow_queries = [
            {"query": "SELECT * FROM incidents WHERE service_name = $1 ORDER BY detected_at DESC",
             "avg_time_ms": 850, "calls": 1200, "rows": 50000},
            {"query": "SELECT COUNT(*) FROM metrics WHERE timestamp > $1 GROUP BY service_name",
             "avg_time_ms": 620, "calls": 300, "rows": 100000},
        ]

        for sq in slow_queries:
            if sq["avg_time_ms"] > self.SLOW_QUERY_MS:
                report.findings.append(Finding(
                    category="slow_query",
                    severity="high" if sq["avg_time_ms"] > 1000 else "medium",
                    title=f"Slow query detected ({sq['avg_time_ms']}ms avg)",
                    description=f"Query: {sq['query'][:80]}... averaging {sq['avg_time_ms']}ms over {sq['calls']} calls",
                    evidence=[
                        f"Average execution time: {sq['avg_time_ms']}ms (threshold: {self.SLOW_QUERY_MS}ms)",
                        f"Total calls: {sq['calls']}, rows examined: {sq['rows']}",
                    ],
                    recommendation="Add appropriate indexes or rewrite query to limit scan range",
                    confidence=90,
                ))

        report.metrics_analyzed["slow_queries_found"] = len(slow_queries)

    def _analyze_connection_pool(self, service: str, report: SpecialistReport):
        # Simulated pool stats
        pool = {"active": 18, "idle": 2, "max": 20, "waiting": 5, "avg_wait_ms": 120}
        usage_pct = (pool["active"] / pool["max"]) * 100

        if usage_pct > self.MAX_POOL_USAGE_PCT:
            report.findings.append(Finding(
                category="connection_pool",
                severity="critical" if pool["waiting"] > 0 else "high",
                title=f"Connection pool near exhaustion ({usage_pct:.0f}%)",
                description=f"Active: {pool['active']}/{pool['max']}, waiting: {pool['waiting']}, avg wait: {pool['avg_wait_ms']}ms",
                evidence=[
                    f"Pool utilization: {usage_pct:.0f}% (threshold: {self.MAX_POOL_USAGE_PCT}%)",
                    f"{pool['waiting']} connections waiting with {pool['avg_wait_ms']}ms avg wait",
                ],
                recommendation="Increase max pool size or optimize connection reuse; check for connection leaks",
                confidence=95,
            ))

        report.metrics_analyzed["pool_stats"] = pool

    def _detect_deadlocks(self, service: str, report: SpecialistReport):
        # Simulated deadlock detection
        deadlocks = [
            {"table": "incidents", "lock_type": "RowExclusiveLock", "wait_ms": 2500,
             "blocking_pid": 1234, "waiting_pid": 5678},
        ]

        for dl in deadlocks:
            if dl["wait_ms"] > self.HIGH_LOCK_WAIT_MS:
                report.findings.append(Finding(
                    category="deadlock",
                    severity="critical",
                    title=f"Potential deadlock on {dl['table']} ({dl['wait_ms']}ms)",
                    description=f"Lock type: {dl['lock_type']}, PID {dl['waiting_pid']} blocked by PID {dl['blocking_pid']}",
                    evidence=[
                        f"Lock wait time: {dl['wait_ms']}ms exceeds {self.HIGH_LOCK_WAIT_MS}ms threshold",
                        f"Table: {dl['table']}, Lock: {dl['lock_type']}",
                    ],
                    recommendation="Review transaction ordering; consider advisory locks or reducing transaction scope",
                    confidence=85,
                ))

    def _recommend_indexes(self, service: str, report: SpecialistReport):
        # Simulated index recommendations
        missing_indexes = [
            {"table": "metrics", "columns": ["service_name", "timestamp"],
             "seq_scans": 5000, "estimated_improvement": "85%"},
            {"table": "incidents", "columns": ["status", "severity"],
             "seq_scans": 1200, "estimated_improvement": "60%"},
        ]

        for idx in missing_indexes:
            cols = ", ".join(idx["columns"])
            report.findings.append(Finding(
                category="missing_index",
                severity="medium",
                title=f"Missing index on {idx['table']}({cols})",
                description=f"{idx['seq_scans']} sequential scans detected; index could improve by ~{idx['estimated_improvement']}",
                evidence=[
                    f"Sequential scans: {idx['seq_scans']}",
                    f"Estimated improvement: {idx['estimated_improvement']}",
                ],
                recommendation=f"CREATE INDEX idx_{idx['table']}_{'_'.join(idx['columns'])} ON {idx['table']}({cols})",
                confidence=80,
            ))

    def _check_db_health(self, service: str, report: SpecialistReport):
        health = {
            "active_connections": 18,
            "max_connections": 100,
            "cache_hit_ratio": 0.97,
            "replication_lag_ms": 50,
            "table_bloat_pct": 12,
            "oldest_transaction_age_sec": 30,
        }

        if health["cache_hit_ratio"] < 0.95:
            report.findings.append(Finding(
                category="cache",
                severity="medium",
                title=f"Low cache hit ratio ({health['cache_hit_ratio']:.1%})",
                description="Database buffer cache is not effective enough",
                evidence=[f"Cache hit ratio: {health['cache_hit_ratio']:.1%} (target: >95%)"],
                recommendation="Increase shared_buffers or optimize query patterns",
                confidence=75,
            ))

        if health["table_bloat_pct"] > 20:
            report.findings.append(Finding(
                category="maintenance",
                severity="low",
                title=f"Table bloat at {health['table_bloat_pct']}%",
                description="Dead tuples consuming disk space",
                recommendation="Run VACUUM ANALYZE on affected tables",
                confidence=70,
            ))

        report.metrics_analyzed["db_health"] = health
