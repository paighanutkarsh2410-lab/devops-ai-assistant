"""
Strategy Library: Pre-built remediation strategies for common infrastructure issues.
"""
from typing import Dict, List, Any


class StrategyLibrary:
    """Collection of pre-built remediation strategies."""

    @staticmethod
    def get_all() -> List[Dict[str, Any]]:
        return [
            StrategyLibrary.database_performance_recovery(),
            StrategyLibrary.memory_leak_recovery(),
            StrategyLibrary.api_timeout_recovery(),
            StrategyLibrary.disk_space_recovery(),
            StrategyLibrary.certificate_renewal(),
            StrategyLibrary.connection_pool_recovery(),
            StrategyLibrary.cascading_failure_recovery(),
            StrategyLibrary.high_cpu_recovery(),
        ]

    @staticmethod
    def get_by_issue(issue_type: str) -> Dict[str, Any]:
        mapping = {
            "database_slow": StrategyLibrary.database_performance_recovery,
            "memory_leak": StrategyLibrary.memory_leak_recovery,
            "api_timeout": StrategyLibrary.api_timeout_recovery,
            "disk_full": StrategyLibrary.disk_space_recovery,
            "cert_expiry": StrategyLibrary.certificate_renewal,
            "connection_pool": StrategyLibrary.connection_pool_recovery,
            "cascading_failure": StrategyLibrary.cascading_failure_recovery,
            "high_cpu": StrategyLibrary.high_cpu_recovery,
        }
        factory = mapping.get(issue_type)
        return factory() if factory else {}

    @staticmethod
    def database_performance_recovery() -> Dict[str, Any]:
        return {
            "name": "Database Performance Recovery",
            "description": "Diagnose and fix database performance issues",
            "issue_type": "database_slow",
            "mode": "sequential",
            "estimated_time_min": 10,
            "steps": [
                {"order": 1, "action": "analyze_slow_queries", "on_success": "step_2", "on_failure": "step_5"},
                {"order": 2, "action": "kill_slow_queries", "condition": "query_time > 30",
                 "on_success": "step_3", "on_failure": "step_4",
                 "retry": {"max_retries": 2, "backoff_sec": 5}},
                {"order": 3, "action": "monitor_improvement", "params": {"duration_min": 5},
                 "on_success": "complete", "on_failure": "step_4"},
                {"order": 4, "action": "restart_database_connection_pool",
                 "on_success": "step_3", "on_failure": "step_5"},
                {"order": 5, "action": "escalate_to_human", "params": {"reason": "Automated DB recovery failed"}},
            ],
        }

    @staticmethod
    def memory_leak_recovery() -> Dict[str, Any]:
        return {
            "name": "Memory Leak Recovery",
            "description": "Detect and mitigate memory leaks with graduated response",
            "issue_type": "memory_leak",
            "mode": "sequential",
            "estimated_time_min": 15,
            "steps": [
                {"order": 1, "action": "run_health_check", "on_success": "step_2", "on_failure": "step_5"},
                {"order": 2, "action": "clear_cache", "on_success": "step_3", "on_failure": "step_4"},
                {"order": 3, "action": "monitor_improvement", "params": {"duration_min": 5},
                 "on_success": "complete", "on_failure": "step_4"},
                {"order": 4, "action": "restart_service", "on_success": "step_3", "on_failure": "step_5",
                 "retry": {"max_retries": 2, "backoff_sec": 10}},
                {"order": 5, "action": "scale_service", "params": {"replicas": 3},
                 "on_success": "complete", "on_failure": "step_6"},
                {"order": 6, "action": "escalate_to_human",
                 "params": {"reason": "Memory leak persists after restart and scale"}},
            ],
        }

    @staticmethod
    def api_timeout_recovery() -> Dict[str, Any]:
        return {
            "name": "API Timeout Recovery",
            "description": "Fix API timeout issues with multi-layer approach",
            "issue_type": "api_timeout",
            "mode": "sequential",
            "estimated_time_min": 8,
            "steps": [
                {"order": 1, "action": "run_health_check", "on_success": "step_2", "on_failure": "step_4"},
                {"order": 2, "action": "enable_rate_limiting", "on_success": "step_3", "on_failure": "step_3"},
                {"order": 3, "action": "scale_service", "params": {"replicas": 4},
                 "on_success": "step_4", "on_failure": "step_5"},
                {"order": 4, "action": "monitor_improvement", "params": {"duration_min": 3},
                 "on_success": "complete", "on_failure": "step_5"},
                {"order": 5, "action": "rollback_deployment", "on_success": "step_4", "on_failure": "step_6"},
                {"order": 6, "action": "escalate_to_human",
                 "params": {"reason": "API timeouts persist after scaling and rollback"}},
            ],
        }

    @staticmethod
    def disk_space_recovery() -> Dict[str, Any]:
        return {
            "name": "Disk Space Recovery",
            "description": "Free disk space through graduated cleanup",
            "issue_type": "disk_full",
            "mode": "sequential",
            "estimated_time_min": 5,
            "steps": [
                {"order": 1, "action": "clean_disk_space", "params": {"target": "logs"},
                 "on_success": "step_2", "on_failure": "step_3"},
                {"order": 2, "action": "monitor_improvement", "params": {"duration_min": 2},
                 "on_success": "complete", "on_failure": "step_3"},
                {"order": 3, "action": "clean_disk_space", "params": {"target": "tmp"},
                 "on_success": "step_2", "on_failure": "step_4"},
                {"order": 4, "action": "increase_resources", "params": {"resource": "disk", "amount": "20GB"},
                 "on_success": "complete", "on_failure": "step_5"},
                {"order": 5, "action": "escalate_to_human",
                 "params": {"reason": "Disk cleanup insufficient, manual intervention needed"}},
            ],
        }

    @staticmethod
    def certificate_renewal() -> Dict[str, Any]:
        return {
            "name": "Certificate Renewal",
            "description": "Renew expiring TLS certificates",
            "issue_type": "cert_expiry",
            "mode": "sequential",
            "estimated_time_min": 5,
            "steps": [
                {"order": 1, "action": "rotate_certificates", "on_success": "step_2", "on_failure": "step_3"},
                {"order": 2, "action": "run_health_check", "on_success": "complete", "on_failure": "step_3"},
                {"order": 3, "action": "escalate_to_human",
                 "params": {"reason": "Certificate rotation failed, manual renewal required"}},
            ],
        }

    @staticmethod
    def connection_pool_recovery() -> Dict[str, Any]:
        return {
            "name": "Connection Pool Recovery",
            "description": "Recover from connection pool exhaustion",
            "issue_type": "connection_pool",
            "mode": "sequential",
            "estimated_time_min": 8,
            "steps": [
                {"order": 1, "action": "analyze_slow_queries", "on_success": "step_2", "on_failure": "step_3"},
                {"order": 2, "action": "kill_slow_queries", "on_success": "step_3", "on_failure": "step_3"},
                {"order": 3, "action": "restart_database_connection_pool",
                 "on_success": "step_4", "on_failure": "step_5"},
                {"order": 4, "action": "monitor_improvement", "params": {"duration_min": 3},
                 "on_success": "complete", "on_failure": "step_5"},
                {"order": 5, "action": "restart_service", "on_success": "step_4", "on_failure": "step_6"},
                {"order": 6, "action": "escalate_to_human",
                 "params": {"reason": "Connection pool issues persist after restart"}},
            ],
        }

    @staticmethod
    def cascading_failure_recovery() -> Dict[str, Any]:
        return {
            "name": "Cascading Failure Recovery",
            "description": "Stop cascade and recover services in dependency order",
            "issue_type": "cascading_failure",
            "mode": "sequential",
            "estimated_time_min": 20,
            "steps": [
                {"order": 1, "action": "enable_rate_limiting",
                 "params": {"services": "all"}, "on_success": "step_2", "on_failure": "step_2"},
                {"order": 2, "action": "restart_service",
                 "params": {"service": "upstream"}, "on_success": "step_3", "on_failure": "step_5"},
                {"order": 3, "action": "run_health_check",
                 "params": {"service": "upstream"}, "on_success": "step_4", "on_failure": "step_5"},
                {"order": 4, "action": "restart_service",
                 "params": {"service": "downstream"}, "on_success": "step_5", "on_failure": "step_6"},
                {"order": 5, "action": "monitor_improvement", "params": {"duration_min": 5},
                 "on_success": "complete", "on_failure": "step_6"},
                {"order": 6, "action": "escalate_to_human",
                 "params": {"reason": "Cascading failure recovery incomplete"}},
            ],
        }

    @staticmethod
    def high_cpu_recovery() -> Dict[str, Any]:
        return {
            "name": "High CPU Recovery",
            "description": "Investigate and reduce high CPU usage",
            "issue_type": "high_cpu",
            "mode": "sequential",
            "estimated_time_min": 10,
            "steps": [
                {"order": 1, "action": "run_health_check", "on_success": "step_2", "on_failure": "step_4"},
                {"order": 2, "action": "scale_service", "params": {"replicas": 3},
                 "on_success": "step_3", "on_failure": "step_4"},
                {"order": 3, "action": "monitor_improvement", "params": {"duration_min": 5},
                 "on_success": "complete", "on_failure": "step_4"},
                {"order": 4, "action": "disable_feature_flag",
                 "params": {"flag": "expensive_computation"}, "on_success": "step_3", "on_failure": "step_5"},
                {"order": 5, "action": "escalate_to_human",
                 "params": {"reason": "High CPU persists, manual profiling needed"}},
            ],
        }
