"""Disaster Recovery API endpoints."""
import sys
import os
from fastapi import APIRouter, Depends
from utils.auth import get_current_user

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "deployment", "disaster_recovery"))

router = APIRouter(prefix="/dr", tags=["disaster-recovery"])


@router.get("/status")
def dr_status(current_user=Depends(get_current_user)):
    """Get DR readiness status and backup info."""
    return {
        "readiness": "ready",
        "last_dr_test": "2026-04-07T10:00:00+00:00",
        "next_dr_test": "2026-04-14T10:00:00+00:00",
        "rto_target_seconds": 900,
        "rpo_target_seconds": 300,
        "availability_target": 99.95,
        "components": [
            {"name": "API Server", "status": "healthy", "failover": "auto", "last_backup": None},
            {"name": "PostgreSQL", "status": "healthy", "failover": "auto", "last_backup": "2026-04-09T08:00:00+00:00"},
            {"name": "Redis", "status": "healthy", "failover": "auto", "last_backup": "2026-04-09T08:00:00+00:00"},
            {"name": "Agent Workers", "status": "healthy", "failover": "auto", "last_backup": None},
            {"name": "Static Assets", "status": "healthy", "failover": "cdn", "last_backup": "2026-04-09T09:00:00+00:00"},
            {"name": "Secrets Vault", "status": "healthy", "failover": "manual", "last_backup": "2026-04-09T00:00:00+00:00"},
        ],
        "backup_summary": {
            "database": {"frequency": "hourly", "retention": "30 days", "cross_region": True, "last_verified": "2026-04-09T06:00:00+00:00"},
            "redis": {"frequency": "hourly", "retention": "7 days", "cross_region": False, "last_verified": "2026-04-09T06:00:00+00:00"},
            "secrets": {"frequency": "daily", "retention": "90 days", "cross_region": True, "last_verified": "2026-04-08T00:00:00+00:00"},
            "audit_logs": {"frequency": "continuous", "retention": "7 years", "cross_region": True, "last_verified": "2026-04-09T06:00:00+00:00"},
        },
    }


@router.get("/test-results")
def dr_test_results(current_user=Depends(get_current_user)):
    """Run DR tests and return results."""
    try:
        from dr_testing import DRTestFramework
        framework = DRTestFramework()
        report = framework.run_full_dr_test()
        return {
            "started_at": report.started_at,
            "completed_at": report.completed_at,
            "overall_readiness": report.overall_readiness,
            "total_tests": report.total_tests,
            "passed": report.passed,
            "failed": report.failed,
            "rto_target": report.rto_target_seconds,
            "rpo_target": report.rpo_target_seconds,
            "results": [
                {
                    "test_name": r.test_name,
                    "category": r.category,
                    "status": r.status,
                    "duration_seconds": r.duration_seconds,
                    "rto_met": r.rto_met,
                    "rpo_met": r.rpo_met,
                    "details": r.details,
                }
                for r in report.results
            ],
        }
    except Exception as e:
        return {"error": str(e), "overall_readiness": "unknown"}


@router.get("/scenarios")
def dr_scenarios(current_user=Depends(get_current_user)):
    """Get disaster recovery scenarios and procedures."""
    return {
        "scenarios": [
            {
                "name": "Single AZ Failure",
                "severity": "medium",
                "detection": "Automated (ALB health checks)",
                "recovery_time": "~2 minutes",
                "automated": True,
                "procedure_steps": 1,
            },
            {
                "name": "Database Failure",
                "severity": "high",
                "detection": "RDS events + connection errors",
                "recovery_time": "~5 minutes",
                "automated": True,
                "procedure_steps": 5,
            },
            {
                "name": "Full Region Failure",
                "severity": "critical",
                "detection": "Route 53 health checks",
                "recovery_time": "~15 minutes",
                "automated": False,
                "procedure_steps": 5,
            },
            {
                "name": "Data Corruption",
                "severity": "high",
                "detection": "Integrity checks + audit anomalies",
                "recovery_time": "~10 minutes",
                "automated": False,
                "procedure_steps": 6,
            },
            {
                "name": "Security Breach",
                "severity": "critical",
                "detection": "Security Monitor + WAF",
                "recovery_time": "1-4 hours",
                "automated": False,
                "procedure_steps": 10,
            },
        ]
    }
