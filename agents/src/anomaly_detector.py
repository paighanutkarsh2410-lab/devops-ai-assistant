"""
Anomaly detection algorithms for metric analysis.
Supports Z-score, moving average, and threshold-based detection.
"""
import numpy as np
from collections import defaultdict
from typing import Optional


class AnomalyDetector:
    def __init__(self, z_threshold: float = 2.5, window_size: int = 20):
        self.z_threshold = z_threshold
        self.window_size = window_size
        # Store history per (service, metric) key
        self._history = defaultdict(list)

    def add_value(self, service: str, metric: str, value: float):
        """Record a new value for a service/metric pair."""
        key = f"{service}:{metric}"
        self._history[key].append(value)
        # Keep only last N*2 values
        max_len = self.window_size * 3
        if len(self._history[key]) > max_len:
            self._history[key] = self._history[key][-max_len:]

    def detect(self, service: str, metric: str, value: float) -> Optional[dict]:
        """
        Run all anomaly detection methods on a value.
        Returns anomaly info dict or None if normal.
        """
        self.add_value(service, metric, value)

        key = f"{service}:{metric}"
        history = self._history[key]

        if len(history) < self.window_size:
            return None  # Not enough data

        # Run detection methods
        z_result = self._zscore_detect(history, value)
        ma_result = self._moving_average_detect(history, value)
        threshold_result = self._threshold_detect(metric, value)

        # Combine results -- any method flagging it is enough
        methods_triggered = []
        max_score = 0.0

        if z_result:
            methods_triggered.append("z-score")
            max_score = max(max_score, z_result["score"])
        if ma_result:
            methods_triggered.append("moving-average")
            max_score = max(max_score, ma_result["score"])
        if threshold_result:
            methods_triggered.append("threshold")
            max_score = max(max_score, threshold_result["score"])

        if not methods_triggered:
            return None

        return {
            "service": service,
            "metric": metric,
            "value": value,
            "methods": methods_triggered,
            "score": max_score,
            "severity": self._score_to_severity(max_score),
            "baseline_avg": float(np.mean(history[-self.window_size:])),
            "baseline_std": float(np.std(history[-self.window_size:])),
        }

    def _zscore_detect(self, history: list, value: float) -> Optional[dict]:
        """Z-score based anomaly detection."""
        window = history[-self.window_size:]
        mean = np.mean(window)
        std = np.std(window)

        if std == 0:
            return None

        z_score = abs(value - mean) / std
        if z_score > self.z_threshold:
            return {"score": min(z_score / self.z_threshold, 3.0)}
        return None

    def _moving_average_detect(self, history: list, value: float) -> Optional[dict]:
        """Moving average deviation detection."""
        window = history[-self.window_size:]
        ma = np.mean(window)
        deviation = abs(value - ma) / max(ma, 1.0)

        # Flag if value deviates more than 50% from moving average
        if deviation > 0.5:
            return {"score": min(deviation * 2, 3.0)}
        return None

    def _threshold_detect(self, metric: str, value: float) -> Optional[dict]:
        """Static threshold detection for known metrics."""
        thresholds = {
            "cpu": {"warning": 80, "critical": 95},
            "memory": {"warning": 85, "critical": 95},
            "error_rate": {"warning": 5, "critical": 10},
            "response_time": {"warning": 500, "critical": 1000},
        }

        limits = thresholds.get(metric)
        if not limits:
            return None

        if value >= limits["critical"]:
            return {"score": 3.0}
        elif value >= limits["warning"]:
            return {"score": 2.0}
        return None

    def _score_to_severity(self, score: float) -> str:
        if score >= 2.5:
            return "critical"
        elif score >= 1.5:
            return "warning"
        return "info"
