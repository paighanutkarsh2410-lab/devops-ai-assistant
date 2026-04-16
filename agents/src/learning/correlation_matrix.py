"""
Correlation Matrix: Builds and maintains mappings between symptoms,
root causes, solutions, services, and time patterns.
"""
import logging
from typing import Dict, List, Any
from collections import defaultdict

logger = logging.getLogger(__name__)


class CorrelationMatrix:
    """
    Tracks correlations:
      - Symptom → Root Cause
      - Root Cause → Solution
      - Service → Common Issues
      - Time → Incident Type
    """

    def __init__(self):
        self.symptom_to_cause = defaultdict(lambda: defaultdict(int))
        self.cause_to_solution = defaultdict(lambda: defaultdict(int))
        self.service_to_issues = defaultdict(lambda: defaultdict(int))
        self.time_to_type = defaultdict(lambda: defaultdict(int))

    def update_from_incident(self, incident: dict, pattern: dict):
        """Update all correlation matrices with a new incident."""
        service = incident.get("service_name", "unknown")
        root_cause = incident.get("root_cause", "")
        solution = incident.get("solution", "")
        pattern_type = pattern.get("pattern_type", "unknown")
        symptoms = pattern.get("symptoms", {})
        time_info = pattern.get("time_info", {})

        # Symptom → Root Cause
        for symptom_key in self._flatten_symptoms(symptoms):
            if root_cause:
                self.symptom_to_cause[symptom_key][root_cause] += 1

        # Root Cause → Solution
        if root_cause and solution:
            self.cause_to_solution[root_cause][solution] += 1

        # Service → Issue Type
        if service:
            self.service_to_issues[service][pattern_type] += 1

        # Time → Incident Type
        hour_bucket = time_info.get("hour_bucket", "")
        day = time_info.get("day_of_week", "")
        if hour_bucket:
            self.time_to_type[hour_bucket][pattern_type] += 1
        if day:
            self.time_to_type[day][pattern_type] += 1

    def predict_root_cause(self, symptoms: dict) -> List[Dict[str, Any]]:
        """Given symptoms, predict the most likely root cause."""
        cause_scores = defaultdict(float)

        for symptom_key in self._flatten_symptoms(symptoms):
            if symptom_key in self.symptom_to_cause:
                total = sum(self.symptom_to_cause[symptom_key].values())
                for cause, count in self.symptom_to_cause[symptom_key].items():
                    cause_scores[cause] += count / total

        if not cause_scores:
            return []

        max_score = max(cause_scores.values())
        return [
            {
                "root_cause": cause,
                "confidence": round(score / max_score * 100, 1),
                "score": round(score, 3),
            }
            for cause, score in sorted(
                cause_scores.items(), key=lambda x: x[1], reverse=True
            )[:5]
        ]

    def suggest_solution(self, root_cause: str) -> List[Dict[str, Any]]:
        """Given a root cause, suggest the most likely solution."""
        if root_cause not in self.cause_to_solution:
            return []

        total = sum(self.cause_to_solution[root_cause].values())
        return [
            {
                "solution": sol,
                "frequency": count,
                "probability": round(count / total * 100, 1),
            }
            for sol, count in sorted(
                self.cause_to_solution[root_cause].items(),
                key=lambda x: x[1],
                reverse=True,
            )[:5]
        ]

    def get_service_profile(self, service_name: str) -> Dict[str, Any]:
        """Get common issues for a service."""
        if service_name not in self.service_to_issues:
            return {"service": service_name, "issues": []}

        total = sum(self.service_to_issues[service_name].values())
        return {
            "service": service_name,
            "total_incidents": total,
            "issues": [
                {
                    "pattern_type": ptype,
                    "count": count,
                    "percentage": round(count / total * 100, 1),
                }
                for ptype, count in sorted(
                    self.service_to_issues[service_name].items(),
                    key=lambda x: x[1],
                    reverse=True,
                )
            ],
        }

    def get_time_insights(self) -> Dict[str, List[Dict]]:
        """Get incident distribution by time."""
        result = {}
        for time_key, type_counts in self.time_to_type.items():
            total = sum(type_counts.values())
            result[time_key] = [
                {"pattern_type": ptype, "count": count, "percentage": round(count / total * 100, 1)}
                for ptype, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True)
            ]
        return result

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the correlation matrix."""
        return {
            "symptom_to_cause": {k: dict(v) for k, v in self.symptom_to_cause.items()},
            "cause_to_solution": {k: dict(v) for k, v in self.cause_to_solution.items()},
            "service_to_issues": {k: dict(v) for k, v in self.service_to_issues.items()},
            "time_to_type": {k: dict(v) for k, v in self.time_to_type.items()},
        }

    def _flatten_symptoms(self, symptoms: dict) -> List[str]:
        """Convert symptom dict into a flat list of symptom keys."""
        keys = []
        for field, value in symptoms.items():
            if isinstance(value, list):
                for item in value:
                    keys.append(f"{field}:{item}")
            elif isinstance(value, str) and value:
                keys.append(f"{field}:{value}")
        return keys
