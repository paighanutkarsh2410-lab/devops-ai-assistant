"""
Recommendation Engine: Suggests the best remediation actions for new incidents
based on historical success data from the knowledge base.
"""
import logging
from typing import List, Dict, Any, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Ranks and recommends remediation actions based on past incident outcomes."""

    def __init__(self, knowledge_base=None, feedback_loop=None):
        self._kb = knowledge_base
        self._feedback = feedback_loop
        self._acceptance_log = []  # track recommendation acceptance

    def recommend_actions(
        self,
        incident: dict,
        similar_incidents: List[dict],
        top_k: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Recommend the best actions for an incident.

        Steps:
          1. Analyze actions from similar incidents
          2. Calculate success rates
          3. Rank by combined score (similarity * success_rate * speed)
          4. Return top-k recommendations
        """
        if not similar_incidents:
            return []

        # Tally actions from similar incidents
        action_data = defaultdict(lambda: {
            "total": 0, "successes": 0, "total_similarity": 0.0,
            "total_duration": 0.0, "durations": [],
        })

        for sim in similar_incidents:
            action = sim.get("action_taken", "") or sim.get("solution", "")
            if not action:
                continue

            score = sim.get("score", 0.5)
            success = sim.get("success", False)
            duration = sim.get("resolution_time", 0) or 0

            action_data[action]["total"] += 1
            action_data[action]["total_similarity"] += score
            if success:
                action_data[action]["successes"] += 1
            if duration > 0:
                action_data[action]["total_duration"] += duration
                action_data[action]["durations"].append(duration)

        if not action_data:
            return []

        # Rank recommendations
        recommendations = []
        for action, data in action_data.items():
            total = data["total"]
            avg_similarity = data["total_similarity"] / total
            success_rate = data["successes"] / total if total > 0 else 0

            # Speed factor: faster resolutions score higher
            avg_duration = (
                data["total_duration"] / len(data["durations"])
                if data["durations"] else 300  # default 5 min
            )
            speed_factor = max(0.1, 1.0 - (avg_duration / 600))  # normalize to 10 min

            # Feedback preference bonus
            preference_bonus = 0
            if self._feedback:
                preference_bonus = self._feedback._action_preferences.get(action, 0) * 0.2

            # Combined score
            combined = (
                avg_similarity * 0.4
                + success_rate * 0.35
                + speed_factor * 0.15
                + preference_bonus * 0.10
            )

            confidence = self._calculate_confidence(success_rate, total, avg_similarity)

            recommendations.append({
                "action_name": action,
                "confidence": round(confidence, 1),
                "success_rate": round(success_rate * 100, 1),
                "similar_count": total,
                "avg_similarity": round(avg_similarity, 3),
                "avg_resolution_time": round(avg_duration, 1),
                "combined_score": round(combined, 4),
            })

        recommendations.sort(key=lambda x: x["combined_score"], reverse=True)
        return recommendations[:top_k]

    def explain_recommendation(
        self, action: str, similar_incidents: List[dict]
    ) -> str:
        """Generate a human-readable explanation for a recommendation."""
        relevant = [s for s in similar_incidents if s.get("action_taken") == action or s.get("solution") == action]

        if not relevant:
            return f"Recommended action: {action} (based on pattern matching)"

        total = len(relevant)
        successes = sum(1 for s in relevant if s.get("success", False))

        # Find most recent use
        timestamps = [s.get("timestamp", "") for s in relevant if s.get("timestamp")]
        latest = max(timestamps) if timestamps else "unknown"

        # Average resolution time
        durations = [s.get("resolution_time", 0) for s in relevant if s.get("resolution_time")]
        avg_time = sum(durations) / len(durations) if durations else 0

        lines = [
            f"This action worked in {successes} out of {total} similar cases.",
        ]
        if avg_time > 0:
            if avg_time < 60:
                lines.append(f"Average resolution time: {avg_time:.0f} seconds.")
            else:
                lines.append(f"Average resolution time: {avg_time / 60:.1f} minutes.")

        if latest != "unknown":
            lines.append(f"Last successful use: {latest[:10]}.")

        return " ".join(lines)

    def get_alternative_actions(
        self,
        incident: dict,
        similar_incidents: List[dict],
        exclude_action: str = "",
    ) -> List[Dict[str, Any]]:
        """Get fallback actions if the primary recommendation fails."""
        all_recs = self.recommend_actions(incident, similar_incidents, top_k=5)
        return [r for r in all_recs if r["action_name"] != exclude_action]

    def log_acceptance(self, action_name: str, accepted: bool, incident_id: str = ""):
        """Track whether a recommendation was accepted by the user/agent."""
        self._acceptance_log.append({
            "action_name": action_name,
            "accepted": accepted,
            "incident_id": incident_id,
        })

    def get_acceptance_rate(self) -> Dict[str, Any]:
        """Calculate how often recommendations are accepted."""
        if not self._acceptance_log:
            return {"total": 0, "accepted": 0, "acceptance_rate": 0}

        total = len(self._acceptance_log)
        accepted = sum(1 for entry in self._acceptance_log if entry["accepted"])

        return {
            "total": total,
            "accepted": accepted,
            "acceptance_rate": round(accepted / total * 100, 1) if total > 0 else 0,
        }

    def _calculate_confidence(
        self, success_rate: float, sample_size: int, avg_similarity: float
    ) -> float:
        """
        Calculate confidence level (0-100) based on multiple factors.

        90-100: Highly confident
        70-89:  Moderately confident
        50-69:  Low confidence
        <50:    Not recommended
        """
        # Base from success rate
        base = success_rate * 60

        # Similarity bonus (up to 20 points)
        sim_bonus = avg_similarity * 20

        # Sample size bonus (up to 20 points, caps at 10 samples)
        sample_bonus = min(sample_size / 10, 1.0) * 20

        return min(100, base + sim_bonus + sample_bonus)
