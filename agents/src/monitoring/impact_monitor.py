"""
Impact Monitor: Tracks metrics before/after remediation to determine if the fix worked.
Returns impact score from -100 (much worse) to +100 (much better).
"""
import time
import logging
from typing import Optional
from .metric_collector import MetricCollector

logger = logging.getLogger(__name__)

# Thresholds for auto-rollback
ROLLBACK_THRESHOLD = -20
WARNING_THRESHOLD = -10


class ImpactResult:
    def __init__(self, score: float, verdict: str, details: dict):
        self.score = score
        self.verdict = verdict  # "success", "warning", "rollback", "neutral"
        self.details = details

    def to_dict(self):
        return {
            "score": round(self.score, 1),
            "verdict": self.verdict,
            "details": self.details,
        }


class ImpactMonitor:
    """Monitors the impact of remediation actions on service metrics."""

    def __init__(self, api_get_fn=None):
        self.collector = MetricCollector(api_get_fn)

    def monitor_action_impact(self, service: str, baseline: dict = None,
                               duration_seconds: int = 30) -> ImpactResult:
        """
        Monitor impact of a remediation action.
        If no baseline provided, collects current metrics as baseline.
        """
        if baseline is None:
            baseline = self.collector.collect_snapshot(service)

        # Wait for metrics to settle
        logger.info(f"[Impact] Monitoring {service} for {duration_seconds}s...")
        time.sleep(min(duration_seconds, 30))

        # Collect current state
        current = self.collector.collect_snapshot(service)

        # Calculate impact
        score, details = self._calculate_impact(baseline, current)

        # Determine verdict
        if score < ROLLBACK_THRESHOLD:
            verdict = "rollback"
        elif score < WARNING_THRESHOLD:
            verdict = "warning"
        elif score > 10:
            verdict = "success"
        else:
            verdict = "neutral"

        result = ImpactResult(score, verdict, details)
        logger.info(f"[Impact] Score: {score:.1f}, Verdict: {verdict}")
        return result

    def _calculate_impact(self, baseline: dict, current: dict) -> tuple:
        """
        Calculate weighted impact score.
        Returns (score, details_dict).
        """
        details = {}
        scores = []
        weights = {
            "error_rate": 3.0,    # Errors are critical
            "response_time": 2.0, # Latency matters a lot
            "cpu": 1.0,           # Resources are secondary
            "memory": 1.0,
        }

        for metric, weight in weights.items():
            before = baseline.get(metric)
            after = current.get(metric)

            if before is not None and after is not None and before > 0:
                # For all these metrics, lower is better
                change_pct = ((before - after) / before) * 100
                weighted = change_pct * weight
                scores.append(weighted)
                details[metric] = {
                    "before": round(before, 2),
                    "after": round(after, 2),
                    "change_pct": round(change_pct, 1),
                    "weighted_score": round(weighted, 1),
                }

        total_weight = sum(weights[m] for m in details)
        overall = sum(scores) / total_weight if total_weight > 0 else 0

        details["overall_score"] = round(overall, 1)
        return overall, details

    def quick_check(self, service: str) -> dict:
        """Quick health check without full monitoring cycle."""
        snapshot = self.collector.collect_snapshot(service)
        healthy = True
        issues = []

        if snapshot.get("error_rate", 0) > 5:
            healthy = False
            issues.append(f"High error rate: {snapshot['error_rate']}")
        if snapshot.get("response_time", 0) > 1000:
            healthy = False
            issues.append(f"High response time: {snapshot['response_time']}ms")
        if snapshot.get("cpu", 0) > 90:
            healthy = False
            issues.append(f"High CPU: {snapshot['cpu']}%")

        return {"healthy": healthy, "metrics": snapshot, "issues": issues}
