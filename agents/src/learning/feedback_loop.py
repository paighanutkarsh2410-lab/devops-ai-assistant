"""
Feedback Loop: Improves the system based on outcomes.
Adjusts detection thresholds, action preferences, and correlation weights.
"""
import logging
import json
import os
from typing import Dict, Any, Optional
from collections import defaultdict
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class FeedbackLoop:
    """Continuously improves detection and remediation based on outcomes."""

    def __init__(self, config_path: str = None):
        self._config_path = config_path or os.path.join(
            os.path.dirname(__file__), '..', '..', 'config', 'auto_tuning.yaml'
        )
        self._data_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'data', 'feedback_state.json'
        )

        # Track outcomes per action+pattern combo
        self._outcomes = defaultdict(lambda: {"successes": 0, "failures": 0, "total": 0})
        # Action preference scores (higher = more preferred)
        self._action_preferences = defaultdict(float)
        # Detection threshold adjustments per metric
        self._threshold_adjustments = {}
        # False positive/negative tracking
        self._detection_stats = {"true_positive": 0, "false_positive": 0, "false_negative": 0, "true_negative": 0}
        # Normal baselines per service+metric
        self._baselines = {}

        self._load_state()

    # ── Core Methods ────────────────────────────────────────────────────

    def record_outcome(
        self, incident_id: str, action_taken: str, success: bool,
        pattern_type: str = "", service_name: str = ""
    ):
        """Record the outcome of a remediation action."""
        key = f"{action_taken}:{pattern_type}" if pattern_type else action_taken

        self._outcomes[key]["total"] += 1
        if success:
            self._outcomes[key]["successes"] += 1
        else:
            self._outcomes[key]["failures"] += 1

        # Update action preference
        self._update_preference(action_taken, success, pattern_type)
        self._save_state()

        logger.info(
            f"Recorded outcome: action={action_taken}, pattern={pattern_type}, "
            f"success={success}"
        )

    def adjust_detection_thresholds(
        self, false_positive_rate: float, false_negative_rate: float,
        metric_name: str = "default"
    ) -> Dict[str, float]:
        """
        Adjust anomaly detection thresholds based on accuracy.

        - Too many false positives → increase threshold (less sensitive)
        - Missing incidents → decrease threshold (more sensitive)
        """
        current = self._threshold_adjustments.get(metric_name, 0.0)

        # Target: false_positive_rate < 10%, false_negative_rate < 5%
        adjustment = 0.0
        if false_positive_rate > 0.15:
            adjustment = 0.1  # Increase threshold (less sensitive)
        elif false_positive_rate > 0.10:
            adjustment = 0.05
        elif false_negative_rate > 0.10:
            adjustment = -0.1  # Decrease threshold (more sensitive)
        elif false_negative_rate > 0.05:
            adjustment = -0.05

        new_value = current + adjustment
        # Clamp to reasonable range
        new_value = max(-1.0, min(1.0, new_value))
        self._threshold_adjustments[metric_name] = new_value

        self._save_state()

        return {
            "metric": metric_name,
            "previous_adjustment": current,
            "new_adjustment": new_value,
            "change": adjustment,
            "reason": (
                "reducing sensitivity (too many false positives)"
                if adjustment > 0 else
                "increasing sensitivity (missing incidents)"
                if adjustment < 0 else
                "no change needed"
            ),
        }

    def update_action_preferences(self) -> Dict[str, float]:
        """
        Recalculate action preference scores based on accumulated outcomes.
        Higher score = more preferred for auto-remediation.
        """
        for key, stats in self._outcomes.items():
            action_name = key.split(":")[0]
            total = stats["total"]
            if total == 0:
                continue

            success_rate = stats["successes"] / total
            # Prefer actions that work AND have enough data
            confidence = min(total / 10, 1.0)  # confidence maxes at 10 samples
            score = success_rate * confidence

            # Penalize failing actions
            if success_rate < 0.3 and total >= 3:
                score *= 0.5

            self._action_preferences[action_name] = max(
                self._action_preferences[action_name], score
            )

        self._save_state()
        return dict(self._action_preferences)

    def improve_correlation_weights(
        self, correct_correlations: int, total_correlations: int
    ) -> Dict[str, Any]:
        """
        Adjust correlation engine weights based on accuracy.
        """
        if total_correlations == 0:
            return {"adjustment": 0, "reason": "no data"}

        accuracy = correct_correlations / total_correlations

        # If accuracy > 80%, increase weight; if < 50%, decrease
        if accuracy > 0.8:
            weight_change = 0.1
        elif accuracy < 0.5:
            weight_change = -0.1
        else:
            weight_change = 0.0

        return {
            "accuracy": round(accuracy * 100, 1),
            "weight_change": weight_change,
            "correct": correct_correlations,
            "total": total_correlations,
        }

    def optimize_resource_allocation(
        self, service_name: str, metric_name: str, values: list
    ) -> Dict[str, Any]:
        """
        Learn normal resource usage per service and update baselines.
        """
        if not values:
            return {}

        import numpy as np

        arr = np.array(values, dtype=float)
        key = f"{service_name}:{metric_name}"

        baseline = {
            "mean": round(float(np.mean(arr)), 2),
            "std": round(float(np.std(arr)), 2),
            "p95": round(float(np.percentile(arr, 95)), 2),
            "min": round(float(np.min(arr)), 2),
            "max": round(float(np.max(arr)), 2),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        self._baselines[key] = baseline
        self._save_state()

        return {
            "service": service_name,
            "metric": metric_name,
            "baseline": baseline,
        }

    def record_detection(self, was_real_incident: bool, was_detected: bool):
        """Track detection accuracy (true positive, false positive, etc.)."""
        if was_detected and was_real_incident:
            self._detection_stats["true_positive"] += 1
        elif was_detected and not was_real_incident:
            self._detection_stats["false_positive"] += 1
        elif not was_detected and was_real_incident:
            self._detection_stats["false_negative"] += 1
        else:
            self._detection_stats["true_negative"] += 1
        self._save_state()

    def get_detection_accuracy(self) -> Dict[str, Any]:
        """Calculate precision, recall, F1 for detection system."""
        tp = self._detection_stats["true_positive"]
        fp = self._detection_stats["false_positive"]
        fn = self._detection_stats["false_negative"]
        tn = self._detection_stats["true_negative"]
        total = tp + fp + fn + tn

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

        return {
            "precision": round(precision * 100, 1),
            "recall": round(recall * 100, 1),
            "f1_score": round(f1 * 100, 1),
            "false_positive_rate": round(fp / total * 100, 1) if total > 0 else 0,
            "false_negative_rate": round(fn / total * 100, 1) if total > 0 else 0,
            "total_evaluations": total,
            "breakdown": self._detection_stats.copy(),
        }

    def get_action_ranking(self, pattern_type: str = "") -> list:
        """Get ranked list of actions by preference for a given pattern."""
        rankings = []
        for key, stats in self._outcomes.items():
            parts = key.split(":")
            action = parts[0]
            pattern = parts[1] if len(parts) > 1 else ""

            if pattern_type and pattern != pattern_type:
                continue

            total = stats["total"]
            if total == 0:
                continue

            success_rate = stats["successes"] / total
            rankings.append({
                "action_name": action,
                "pattern_type": pattern,
                "total": total,
                "success_rate": round(success_rate * 100, 1),
                "preference": round(self._action_preferences.get(action, 0), 3),
            })

        return sorted(rankings, key=lambda x: x["success_rate"], reverse=True)

    def get_threshold_adjustment(self, metric_name: str) -> float:
        """Get the current threshold adjustment for a metric."""
        return self._threshold_adjustments.get(metric_name, 0.0)

    def get_baseline(self, service_name: str, metric_name: str) -> Optional[dict]:
        """Get learned baseline for a service+metric."""
        return self._baselines.get(f"{service_name}:{metric_name}")

    # ── Persistence ─────────────────────────────────────────────────────

    def _save_state(self):
        """Persist feedback state to disk."""
        try:
            os.makedirs(os.path.dirname(self._data_path), exist_ok=True)
            state = {
                "outcomes": dict(self._outcomes),
                "action_preferences": dict(self._action_preferences),
                "threshold_adjustments": self._threshold_adjustments,
                "detection_stats": self._detection_stats,
                "baselines": self._baselines,
                "saved_at": datetime.now(timezone.utc).isoformat(),
            }
            with open(self._data_path, 'w') as f:
                json.dump(state, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save feedback state: {e}")

    def _load_state(self):
        """Load feedback state from disk."""
        try:
            if os.path.exists(self._data_path):
                with open(self._data_path, 'r') as f:
                    state = json.load(f)
                for k, v in state.get("outcomes", {}).items():
                    self._outcomes[k] = v
                self._action_preferences = defaultdict(
                    float, state.get("action_preferences", {})
                )
                self._threshold_adjustments = state.get("threshold_adjustments", {})
                self._detection_stats = state.get("detection_stats", self._detection_stats)
                self._baselines = state.get("baselines", {})
        except Exception as e:
            logger.error(f"Failed to load feedback state: {e}")

    def _update_preference(self, action_name: str, success: bool, pattern_type: str):
        """Adjust action preference score based on outcome."""
        # Reward success, penalize failure
        delta = 0.1 if success else -0.15
        current = self._action_preferences.get(action_name, 0.5)
        self._action_preferences[action_name] = max(0, min(1.0, current + delta))
