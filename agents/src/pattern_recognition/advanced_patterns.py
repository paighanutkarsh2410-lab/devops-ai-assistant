"""
Advanced Pattern Recognizer: Cascading failures, oscillating issues,
slow degradation, correlation patterns, temporal patterns, rare events.
"""
import math
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class PatternMatch:
    pattern_type: str
    confidence: float
    description: str
    evidence: List[str] = field(default_factory=list)
    affected_services: List[str] = field(default_factory=list)
    predicted_next: Optional[str] = None
    severity: str = "medium"


class AdvancedPatternRecognizer:
    """PhD-level pattern recognition for complex incident types."""

    def __init__(self):
        self._incident_cache: List[dict] = []
        self._metric_cache: Dict[str, List[dict]] = defaultdict(list)

    def add_incidents(self, incidents: List[dict]):
        self._incident_cache.extend(incidents)

    def add_metrics(self, service: str, metrics: List[dict]):
        """metrics: list of {timestamp, value, metric_name}"""
        self._metric_cache[service].extend(metrics)

    # ── Cascading Failure Detection ────────────────────────────────────

    def detect_cascading_failures(self, incidents: List[dict] = None) -> List[PatternMatch]:
        """Identify chain reactions: Service A fails → B → C."""
        incidents = incidents or self._incident_cache
        if len(incidents) < 2:
            return []

        # Sort by time
        sorted_inc = sorted(incidents, key=lambda i: i.get("detected_at", ""))
        results = []

        # Build temporal chains: incidents within 15 min of each other
        chains: List[List[dict]] = []
        current_chain = [sorted_inc[0]]

        for i in range(1, len(sorted_inc)):
            prev_time = sorted_inc[i - 1].get("detected_at", "")
            curr_time = sorted_inc[i].get("detected_at", "")

            # Simple time proximity check (within 15 minutes)
            if prev_time and curr_time and prev_time[:15] == curr_time[:15]:
                current_chain.append(sorted_inc[i])
            else:
                if len(current_chain) >= 2:
                    chains.append(current_chain)
                current_chain = [sorted_inc[i]]

        if len(current_chain) >= 2:
            chains.append(current_chain)

        for chain in chains:
            services = [c.get("service_name", "unknown") for c in chain]
            unique_services = list(dict.fromkeys(services))

            if len(unique_services) >= 2:
                root = unique_services[0]
                results.append(PatternMatch(
                    pattern_type="cascading_failure",
                    confidence=min(95, 60 + len(chain) * 10),
                    description=f"Cascade: {' → '.join(unique_services)}",
                    evidence=[
                        f"Root service: {root}",
                        f"Chain length: {len(chain)} incidents across {len(unique_services)} services",
                        f"Time span: {chain[0].get('detected_at', '?')} to {chain[-1].get('detected_at', '?')}",
                    ],
                    affected_services=unique_services,
                    severity="critical" if len(unique_services) >= 3 else "high",
                ))

        return results

    # ── Oscillating Issues ─────────────────────────────────────────────

    def detect_oscillating_issues(self, metrics: List[dict] = None,
                                   service: str = None) -> List[PatternMatch]:
        """Detect problems that come and go periodically."""
        if service and not metrics:
            metrics = self._metric_cache.get(service, [])
        if not metrics or len(metrics) < 20:
            return []

        results = []
        values = [m.get("value", 0) for m in metrics]

        # Detect periodicity using autocorrelation
        n = len(values)
        mean = sum(values) / n
        variance = sum((v - mean) ** 2 for v in values) / n

        if variance == 0:
            return []

        best_period = 0
        best_corr = 0

        for lag in range(2, min(n // 2, 100)):
            corr = sum(
                (values[i] - mean) * (values[i + lag] - mean)
                for i in range(n - lag)
            ) / ((n - lag) * variance)

            if corr > best_corr and corr > 0.5:
                best_corr = corr
                best_period = lag

        if best_period > 0 and best_corr > 0.5:
            # Estimate when next occurrence will happen
            results.append(PatternMatch(
                pattern_type="oscillating",
                confidence=round(best_corr * 100, 1),
                description=f"Periodic pattern every ~{best_period} samples (correlation: {best_corr:.2f})",
                evidence=[
                    f"Period: {best_period} data points",
                    f"Autocorrelation: {best_corr:.3f}",
                    f"Data points analyzed: {n}",
                ],
                predicted_next=f"Next occurrence in ~{best_period} intervals",
                severity="medium",
            ))

        return results

    # ── Slow Degradation ───────────────────────────────────────────────

    def detect_slow_degradation(self, metrics: List[dict] = None,
                                 service: str = None,
                                 days: int = 30) -> List[PatternMatch]:
        """Detect gradual performance decline that isn't obvious day-to-day."""
        if service and not metrics:
            metrics = self._metric_cache.get(service, [])
        if not metrics or len(metrics) < 10:
            return []

        results = []
        values = [m.get("value", 0) for m in metrics]
        n = len(values)

        # Linear regression
        x_mean = (n - 1) / 2
        y_mean = sum(values) / n
        numerator = sum((i - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return []

        slope = numerator / denominator
        intercept = y_mean - slope * x_mean

        # R² value
        ss_res = sum((values[i] - (slope * i + intercept)) ** 2 for i in range(n))
        ss_tot = sum((values[i] - y_mean) ** 2 for i in range(n))
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

        # Significant degradation: positive slope (increasing metric = bad) and good fit
        if slope > 0 and r_squared > 0.5:
            pct_change = (slope * n / max(values[0], 1)) * 100
            if abs(pct_change) > 5:  # >5% total change
                results.append(PatternMatch(
                    pattern_type="slow_degradation",
                    confidence=round(r_squared * 100, 1),
                    description=f"Gradual increase: {pct_change:.1f}% over {n} samples (slope: {slope:.3f}/sample)",
                    evidence=[
                        f"Linear slope: {slope:.4f} per sample",
                        f"R²: {r_squared:.3f} (strong fit)",
                        f"Start: {values[0]:.1f}, End: {values[-1]:.1f}",
                        f"Total change: {pct_change:.1f}%",
                    ],
                    severity="high" if pct_change > 20 else "medium",
                ))

        return results

    # ── Multi-Metric Correlation Patterns ──────────────────────────────

    def detect_correlation_patterns(self, metrics_by_name: Dict[str, List[float]],
                                     threshold: float = 0.7) -> List[PatternMatch]:
        """Detect when multiple metrics move together (composite patterns)."""
        results = []
        names = list(metrics_by_name.keys())

        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                a = metrics_by_name[names[i]]
                b = metrics_by_name[names[j]]
                n = min(len(a), len(b))
                if n < 5:
                    continue

                # Pearson correlation
                a_vals = a[:n]
                b_vals = b[:n]
                a_mean = sum(a_vals) / n
                b_mean = sum(b_vals) / n

                cov = sum((a_vals[k] - a_mean) * (b_vals[k] - b_mean) for k in range(n))
                std_a = math.sqrt(sum((v - a_mean) ** 2 for v in a_vals))
                std_b = math.sqrt(sum((v - b_mean) ** 2 for v in b_vals))

                if std_a == 0 or std_b == 0:
                    continue

                corr = cov / (std_a * std_b)

                if abs(corr) >= threshold:
                    direction = "positive" if corr > 0 else "inverse"
                    results.append(PatternMatch(
                        pattern_type="correlation",
                        confidence=round(abs(corr) * 100, 1),
                        description=f"{direction.title()} correlation between {names[i]} and {names[j]} (r={corr:.2f})",
                        evidence=[
                            f"Pearson r: {corr:.3f}",
                            f"Samples: {n}",
                            f"Direction: {direction}",
                        ],
                        severity="info",
                    ))

        return results

    # ── Temporal Patterns ──────────────────────────────────────────────

    def detect_temporal_patterns(self, incidents: List[dict] = None) -> List[PatternMatch]:
        """Find time-of-day and day-of-week patterns."""
        incidents = incidents or self._incident_cache
        if len(incidents) < 10:
            return []

        results = []
        hour_counts = defaultdict(int)
        dow_counts = defaultdict(int)

        for inc in incidents:
            ts = inc.get("detected_at", "")
            if len(ts) >= 13:
                try:
                    hour = int(ts[11:13])
                    hour_counts[hour] += 1
                except (ValueError, IndexError):
                    pass
            # Approximate day of week from date
            date_str = ts[:10] if len(ts) >= 10 else ""
            if date_str:
                dow_counts[date_str] = dow_counts.get(date_str, 0) + 1

        # Find peak hours
        if hour_counts:
            total = sum(hour_counts.values())
            avg = total / 24
            for hour, count in hour_counts.items():
                if count > avg * 2.5:  # 2.5x the average
                    results.append(PatternMatch(
                        pattern_type="temporal_hour",
                        confidence=min(90, round((count / avg) * 30, 1)),
                        description=f"Incident spike at {hour:02d}:00 ({count} incidents, {count/avg:.1f}x average)",
                        evidence=[
                            f"Count at {hour:02d}:00: {count}",
                            f"Average per hour: {avg:.1f}",
                            f"Ratio: {count/avg:.1f}x",
                        ],
                        severity="medium",
                    ))

        return results

    # ── Rare Event Detection ───────────────────────────────────────────

    def detect_rare_events(self, metrics: List[dict] = None,
                            service: str = None,
                            z_threshold: float = 3.5) -> List[PatternMatch]:
        """Detect statistical outliers / black swan events."""
        if service and not metrics:
            metrics = self._metric_cache.get(service, [])
        if not metrics or len(metrics) < 20:
            return []

        results = []
        values = [m.get("value", 0) for m in metrics]
        n = len(values)
        mean = sum(values) / n
        std = math.sqrt(sum((v - mean) ** 2 for v in values) / n)

        if std == 0:
            return []

        for i, m in enumerate(metrics):
            z = abs(m.get("value", 0) - mean) / std
            if z > z_threshold:
                results.append(PatternMatch(
                    pattern_type="rare_event",
                    confidence=min(99, round(z * 20, 1)),
                    description=f"Statistical outlier: value={m.get('value', 0):.1f} (z-score: {z:.1f})",
                    evidence=[
                        f"Value: {m.get('value', 0):.1f}",
                        f"Mean: {mean:.1f}, Std: {std:.1f}",
                        f"Z-score: {z:.2f} (threshold: {z_threshold})",
                        f"Probability: <{(1 - 0.9997) * 100:.4f}%",
                    ],
                    severity="critical" if z > 5 else "high",
                ))

        return results

    # ── Run All Detectors ──────────────────────────────────────────────

    def run_all_detectors(self, incidents: List[dict] = None,
                          metrics: Dict[str, List[dict]] = None) -> dict:
        """Run all pattern detection algorithms and return combined results."""
        if incidents:
            self.add_incidents(incidents)
        if metrics:
            for svc, data in metrics.items():
                self.add_metrics(svc, data)

        all_patterns = []
        all_patterns.extend(self.detect_cascading_failures())
        all_patterns.extend(self.detect_temporal_patterns())

        for service, data in self._metric_cache.items():
            all_patterns.extend(self.detect_oscillating_issues(service=service))
            all_patterns.extend(self.detect_slow_degradation(service=service))
            all_patterns.extend(self.detect_rare_events(service=service))

        # Sort by confidence
        all_patterns.sort(key=lambda p: -p.confidence)

        return {
            "total_patterns": len(all_patterns),
            "by_type": {
                ptype: [p for p in all_patterns if p.pattern_type == ptype]
                for ptype in set(p.pattern_type for p in all_patterns)
            },
            "critical": [p for p in all_patterns if p.severity == "critical"],
            "high": [p for p in all_patterns if p.severity == "high"],
        }
