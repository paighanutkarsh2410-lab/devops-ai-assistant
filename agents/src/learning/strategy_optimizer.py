"""
Strategy Optimizer: Optimizes detection thresholds, remediation ordering,
and per-environment preferences through historical analysis.
"""
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class ThresholdConfig:
    metric: str
    service: str
    current_value: float
    recommended_value: float
    false_positive_rate: float
    false_negative_rate: float
    f1_score: float


@dataclass
class ActionRanking:
    action: str
    success_rate: float
    avg_resolution_time_sec: float
    total_attempts: int
    score: float  # composite ranking score


class StrategyOptimizer:
    """Optimizes agent strategies using historical outcome data."""

    def __init__(self):
        self._detection_history: List[dict] = []
        # {metric, service, threshold, actual_value, was_true_positive, was_false_positive}
        self._remediation_history: List[dict] = []
        # {action, service, incident_type, success, resolution_time_sec}
        self._environment_prefs: Dict[str, Dict] = defaultdict(dict)
        # per-environment learned preferences

    # ── Detection Threshold Optimization ───────────────────────────────

    def record_detection(self, metric: str, service: str, threshold: float,
                         actual_value: float, was_incident: bool, was_alerted: bool):
        """Record a detection event for threshold tuning."""
        self._detection_history.append({
            "metric": metric, "service": service,
            "threshold": threshold, "actual_value": actual_value,
            "true_positive": was_incident and was_alerted,
            "false_positive": not was_incident and was_alerted,
            "false_negative": was_incident and not was_alerted,
            "true_negative": not was_incident and not was_alerted,
        })

    def optimize_detection_thresholds(self, service: str = None) -> List[ThresholdConfig]:
        """Find optimal thresholds that minimize false positives while catching real incidents."""
        # Group by (metric, service)
        grouped: Dict[Tuple[str, str], List[dict]] = defaultdict(list)
        for record in self._detection_history:
            if service and record["service"] != service:
                continue
            key = (record["metric"], record["service"])
            grouped[key].append(record)

        results = []
        for (metric, svc), records in grouped.items():
            if len(records) < 10:
                continue

            tp = sum(1 for r in records if r["true_positive"])
            fp = sum(1 for r in records if r["false_positive"])
            fn = sum(1 for r in records if r["false_negative"])
            tn = sum(1 for r in records if r["true_negative"])

            total = len(records)
            fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
            fnr = fn / (fn + tp) if (fn + tp) > 0 else 0
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

            # Recommend threshold adjustment
            current_threshold = records[-1]["threshold"]
            if fpr > 0.15:
                # Too many false positives → raise threshold
                recommended = current_threshold * 1.15
            elif fnr > 0.10:
                # Missing real incidents → lower threshold
                recommended = current_threshold * 0.85
            else:
                recommended = current_threshold

            results.append(ThresholdConfig(
                metric=metric, service=svc,
                current_value=current_threshold,
                recommended_value=round(recommended, 2),
                false_positive_rate=round(fpr * 100, 1),
                false_negative_rate=round(fnr * 100, 1),
                f1_score=round(f1 * 100, 1),
            ))

        return results

    # ── Remediation Order Optimization ─────────────────────────────────

    def record_remediation(self, action: str, service: str,
                            incident_type: str, success: bool,
                            resolution_time_sec: float):
        """Record a remediation attempt for action ranking."""
        self._remediation_history.append({
            "action": action, "service": service,
            "incident_type": incident_type,
            "success": success,
            "resolution_time_sec": resolution_time_sec,
        })

    def optimize_remediation_order(self, incident_type: str = None,
                                    service: str = None) -> List[ActionRanking]:
        """Rank remediation actions by effectiveness and speed."""
        filtered = self._remediation_history
        if incident_type:
            filtered = [r for r in filtered if r["incident_type"] == incident_type]
        if service:
            filtered = [r for r in filtered if r["service"] == service]

        # Group by action
        action_data: Dict[str, List[dict]] = defaultdict(list)
        for record in filtered:
            action_data[record["action"]].append(record)

        rankings = []
        for action, records in action_data.items():
            total = len(records)
            successes = sum(1 for r in records if r["success"])
            success_rate = (successes / total * 100) if total > 0 else 0
            avg_time = (
                sum(r["resolution_time_sec"] for r in records if r["success"])
                / max(successes, 1)
            )

            # Composite score: success_rate * 0.6 + speed * 0.3 + sample_size * 0.1
            speed_score = max(0, 100 - avg_time / 6)  # 600s = 0 score
            sample_bonus = min(10, total)  # Bonus for more data
            score = success_rate * 0.6 + speed_score * 0.3 + sample_bonus

            rankings.append(ActionRanking(
                action=action,
                success_rate=round(success_rate, 1),
                avg_resolution_time_sec=round(avg_time, 1),
                total_attempts=total,
                score=round(score, 1),
            ))

        rankings.sort(key=lambda r: -r.score)
        return rankings

    # ── Environment Personalization ────────────────────────────────────

    def set_environment_preference(self, environment: str, key: str, value):
        """Store learned preference for a specific environment."""
        self._environment_prefs[environment][key] = value

    def get_environment_preferences(self, environment: str) -> dict:
        return dict(self._environment_prefs.get(environment, {}))

    def learn_risk_tolerance(self, environment: str, history: List[dict]) -> dict:
        """Learn risk tolerance from past approval/rejection patterns."""
        approved = [h for h in history if h.get("approved")]
        rejected = [h for h in history if not h.get("approved")]

        max_approved_risk = max(
            (h.get("risk_level", 0) for h in approved), default=0
        )
        avg_response_time = (
            sum(h.get("response_time_sec", 0) for h in approved) / max(len(approved), 1)
        )

        tolerance = {
            "auto_approve_below_risk": min(max_approved_risk, 3),
            "avg_approval_time_sec": round(avg_response_time, 1),
            "approval_rate": round(len(approved) / max(len(history), 1) * 100, 1),
            "total_decisions": len(history),
        }

        self._environment_prefs[environment]["risk_tolerance"] = tolerance
        return tolerance

    # ── Meta-Learning ──────────────────────────────────────────────────

    def identify_important_features(self) -> dict:
        """Determine which features are most predictive of successful outcomes."""
        if len(self._remediation_history) < 20:
            return {"status": "insufficient_data", "min_required": 20}

        # Analyze which factors correlate with success
        feature_importance = {}

        # Service-specific success rates
        service_success: Dict[str, List[bool]] = defaultdict(list)
        type_success: Dict[str, List[bool]] = defaultdict(list)
        action_success: Dict[str, List[bool]] = defaultdict(list)

        for r in self._remediation_history:
            service_success[r["service"]].append(r["success"])
            type_success[r["incident_type"]].append(r["success"])
            action_success[r["action"]].append(r["success"])

        # Variance in success rates = importance
        def variance(groups):
            rates = [sum(v) / len(v) for v in groups.values() if len(v) >= 3]
            if len(rates) < 2:
                return 0
            mean = sum(rates) / len(rates)
            return sum((r - mean) ** 2 for r in rates) / len(rates)

        feature_importance["service"] = round(variance(service_success) * 100, 2)
        feature_importance["incident_type"] = round(variance(type_success) * 100, 2)
        feature_importance["action_choice"] = round(variance(action_success) * 100, 2)

        # Rank
        ranked = sorted(feature_importance.items(), key=lambda x: -x[1])

        return {
            "feature_importance": dict(ranked),
            "most_important": ranked[0][0] if ranked else None,
            "recommendation": self._meta_recommendation(ranked),
        }

    def _meta_recommendation(self, ranked: List[tuple]) -> str:
        if not ranked:
            return "Not enough data for recommendations"
        top = ranked[0][0]
        if top == "service":
            return "Success varies most by service — focus on per-service tuning"
        elif top == "incident_type":
            return "Incident type is most predictive — build type-specific playbooks"
        elif top == "action_choice":
            return "Action selection matters most — optimize remediation ordering"
        return "Continue collecting data for better insights"

    # ── Dashboard Data ─────────────────────────────────────────────────

    def get_optimization_summary(self) -> dict:
        return {
            "detection_records": len(self._detection_history),
            "remediation_records": len(self._remediation_history),
            "threshold_recommendations": [
                {"metric": t.metric, "service": t.service,
                 "current": t.current_value, "recommended": t.recommended_value,
                 "f1_score": t.f1_score}
                for t in self.optimize_detection_thresholds()
            ],
            "top_actions": [
                {"action": r.action, "success_rate": r.success_rate,
                 "avg_time": r.avg_resolution_time_sec, "score": r.score}
                for r in self.optimize_remediation_order()[:5]
            ],
            "feature_importance": self.identify_important_features(),
            "environments": {
                env: prefs for env, prefs in self._environment_prefs.items()
            },
        }
