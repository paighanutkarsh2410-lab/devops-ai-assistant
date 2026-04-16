"""
Load Test Results Analyzer: Parses k6 output, compares to benchmarks,
identifies regressions, and generates performance reports.
"""
import json
import logging
import os
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


@dataclass
class PerformanceRegression:
    metric: str
    baseline: float
    current: float
    change_percent: float
    severity: str  # critical, warning, info


class ResultsAnalyzer:
    """Analyze k6 load test results and track performance trends."""

    BENCHMARKS = {
        "http_req_duration_p95": {"target": 200, "unit": "ms", "direction": "lower"},
        "http_req_duration_p99": {"target": 500, "unit": "ms", "direction": "lower"},
        "http_req_failed_rate": {"target": 0.01, "unit": "%", "direction": "lower"},
        "http_reqs_rate": {"target": 500, "unit": "req/s", "direction": "higher"},
        "iteration_duration_p95": {"target": 5000, "unit": "ms", "direction": "lower"},
    }

    def __init__(self, baseline_file: str = None):
        self._baseline: Dict[str, float] = {}
        self._history: List[Dict[str, Any]] = []
        if baseline_file and os.path.exists(baseline_file):
            with open(baseline_file) as f:
                self._baseline = json.load(f)

    def parse_k6_summary(self, summary_file: str) -> Dict[str, Any]:
        """Parse k6 --summary-export JSON file."""
        if not os.path.exists(summary_file):
            logger.error(f"Summary file not found: {summary_file}")
            return {}

        with open(summary_file) as f:
            data = json.load(f)

        metrics = data.get("metrics", {})
        parsed = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics": {},
        }

        for metric_name, values in metrics.items():
            if isinstance(values, dict) and "values" in values:
                parsed["metrics"][metric_name] = values["values"]
            elif isinstance(values, dict):
                parsed["metrics"][metric_name] = values

        return parsed

    def parse_k6_json_stream(self, json_file: str) -> List[Dict[str, Any]]:
        """Parse k6 JSON output stream (line-delimited JSON)."""
        data_points = []
        if not os.path.exists(json_file):
            return data_points

        with open(json_file) as f:
            for line in f:
                try:
                    point = json.loads(line.strip())
                    if point.get("type") == "Point":
                        data_points.append(point)
                except json.JSONDecodeError:
                    continue

        return data_points

    def check_benchmarks(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Compare metrics against performance benchmarks."""
        results = {}

        for benchmark, config in self.BENCHMARKS.items():
            parts = benchmark.split("_")
            metric_key = "_".join(parts[:-1])
            stat = parts[-1]

            metric_data = metrics.get(metric_key, {})
            if isinstance(metric_data, dict):
                actual = metric_data.get(stat, metric_data.get("value", None))
            else:
                actual = metric_data

            if actual is None:
                results[benchmark] = {"status": "no_data", "target": config["target"]}
                continue

            if config["direction"] == "lower":
                passed = actual <= config["target"]
            else:
                passed = actual >= config["target"]

            results[benchmark] = {
                "target": config["target"],
                "actual": round(actual, 2) if isinstance(actual, float) else actual,
                "unit": config["unit"],
                "passed": passed,
                "margin": round(((config["target"] - actual) / config["target"]) * 100, 1),
            }

        return results

    def detect_regressions(self, current_metrics: Dict[str, Any],
                           threshold_percent: float = 10.0) -> List[PerformanceRegression]:
        """Detect performance regressions compared to baseline."""
        regressions = []

        for metric, baseline_val in self._baseline.items():
            current_val = current_metrics.get(metric)
            if current_val is None or baseline_val == 0:
                continue

            change = ((current_val - baseline_val) / baseline_val) * 100
            bench = self.BENCHMARKS.get(metric, {})
            direction = bench.get("direction", "lower")

            # For "lower is better" metrics, positive change = regression
            # For "higher is better" metrics, negative change = regression
            is_regression = (direction == "lower" and change > threshold_percent) or \
                            (direction == "higher" and change < -threshold_percent)

            if is_regression:
                severity = "critical" if abs(change) > 50 else "warning" if abs(change) > 20 else "info"
                regressions.append(PerformanceRegression(
                    metric=metric,
                    baseline=baseline_val,
                    current=current_val,
                    change_percent=round(change, 1),
                    severity=severity,
                ))

        return regressions

    def generate_report(self, summary_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive performance analysis report."""
        metrics = summary_data.get("metrics", {})
        benchmarks = self.check_benchmarks(metrics)
        regressions = self.detect_regressions(
            {k: v.get("actual", 0) for k, v in benchmarks.items() if isinstance(v, dict) and "actual" in v}
        )

        all_passed = all(
            r.get("passed", True) for r in benchmarks.values() if isinstance(r, dict)
        )
        critical_regressions = [r for r in regressions if r.severity == "critical"]

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "overall_status": "pass" if all_passed and not critical_regressions else "fail",
            "benchmarks": benchmarks,
            "regressions": [
                {
                    "metric": r.metric,
                    "baseline": r.baseline,
                    "current": r.current,
                    "change_percent": r.change_percent,
                    "severity": r.severity,
                }
                for r in regressions
            ],
            "summary": {
                "benchmarks_total": len(benchmarks),
                "benchmarks_passed": sum(1 for r in benchmarks.values() if isinstance(r, dict) and r.get("passed", True)),
                "regressions_found": len(regressions),
                "critical_regressions": len(critical_regressions),
            },
            "recommendations": self._generate_recommendations(benchmarks, regressions),
        }

    def _generate_recommendations(self, benchmarks: Dict, regressions: List) -> List[str]:
        """Generate optimization recommendations."""
        recs = []

        for name, result in benchmarks.items():
            if isinstance(result, dict) and not result.get("passed", True):
                if "duration" in name:
                    recs.append(f"Optimize {name}: {result['actual']}{result['unit']} exceeds target {result['target']}{result['unit']}. Consider caching, query optimization, or connection pooling.")
                elif "failed" in name:
                    recs.append(f"Reduce error rate: {result['actual']}% exceeds {result['target']}% target. Check error logs, increase timeouts, or add retry logic.")
                elif "rate" in name:
                    recs.append(f"Improve throughput: {result['actual']} req/s below {result['target']} req/s target. Consider horizontal scaling or async processing.")

        for reg in regressions:
            if reg.severity == "critical":
                recs.append(f"CRITICAL regression in {reg.metric}: {reg.change_percent}% worse than baseline. Investigate recent changes.")

        if not recs:
            recs.append("All benchmarks passing. System performance is within expected parameters.")

        return recs

    def save_baseline(self, metrics: Dict[str, Any], output_file: str):
        """Save current metrics as new baseline."""
        with open(output_file, 'w') as f:
            json.dump(metrics, f, indent=2)
        logger.info(f"Baseline saved to {output_file}")
