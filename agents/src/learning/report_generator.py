"""
Learning Report Generator: Creates automated reports showing system improvement.
Generates weekly/monthly summaries, insights, and knowledge gap analysis.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class LearningReportGenerator:
    """Generates learning progress reports and insights."""

    def __init__(self, api_get=None, api_post=None):
        self._api_get = api_get
        self._api_post = api_post

    def generate_weekly_report(self) -> Dict[str, Any]:
        """Generate a weekly learning summary report."""
        stats = self._get_stats()
        outcome_stats = self._get_outcome_stats()
        patterns = self._get_patterns()

        # Build insights
        insights = self._generate_insights(stats, outcome_stats, patterns)

        return {
            "report_type": "weekly",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "incidents_learned": stats.get("total_outcomes_tracked", 0),
                "patterns_discovered": stats.get("total_patterns_discovered", 0),
                "overall_success_rate": stats.get("overall_success_rate", 0),
                "avg_resolution_time": stats.get("avg_resolution_time_seconds", 0),
                "most_effective_action": stats.get("most_effective_action"),
                "recommendation_accuracy": stats.get("recommendation_accuracy", 0),
            },
            "action_stats": outcome_stats,
            "pattern_count": len(patterns),
            "insights": insights,
            "knowledge_gaps": self._identify_knowledge_gaps(outcome_stats, patterns),
        }

    def generate_monthly_report(self) -> Dict[str, Any]:
        """Generate a monthly trend analysis report."""
        weekly = self.generate_weekly_report()

        return {
            "report_type": "monthly",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "summary": weekly["summary"],
            "trends": {
                "success_rate_trend": "improving",  # placeholder
                "resolution_time_trend": "improving",
                "pattern_discovery_rate": weekly["pattern_count"],
            },
            "action_stats": weekly["action_stats"],
            "insights": weekly["insights"],
            "knowledge_gaps": weekly["knowledge_gaps"],
            "recommendations_for_improvement": self._improvement_recommendations(
                weekly["action_stats"], weekly["knowledge_gaps"]
            ),
        }

    def generate_learning_insights(self) -> List[str]:
        """Generate human-readable insights about system learning progress."""
        stats = self._get_stats()
        outcome_stats = self._get_outcome_stats()

        insights = []

        total_patterns = stats.get("total_patterns_discovered", 0)
        if total_patterns > 0:
            insights.append(f"System has learned {total_patterns} distinct incident patterns.")

        success_rate = stats.get("overall_success_rate", 0)
        if success_rate > 0:
            if success_rate >= 80:
                insights.append(f"Detection accuracy is excellent at {success_rate}%.")
            elif success_rate >= 60:
                insights.append(f"Detection accuracy is good at {success_rate}%, with room to improve.")
            else:
                insights.append(f"Detection accuracy is {success_rate}% — more training data needed.")

        avg_time = stats.get("avg_resolution_time_seconds", 0)
        if avg_time > 0:
            if avg_time < 60:
                insights.append(f"Average resolution time: {avg_time:.0f} seconds (excellent).")
            elif avg_time < 300:
                insights.append(f"Average resolution time: {avg_time / 60:.1f} minutes.")
            else:
                insights.append(f"Average resolution time: {avg_time / 60:.1f} minutes — consider optimizing.")

        best_action = stats.get("most_effective_action")
        if best_action:
            insights.append(f"Most effective action: {best_action}.")

        # Action-specific insights
        for stat in outcome_stats[:3]:
            name = stat.get("action_name", "")
            rate = stat.get("success_rate", 0)
            total = stat.get("total", 0)
            if total >= 3:
                insights.append(
                    f"{name}: {rate}% success rate across {total} uses."
                )

        rec_accuracy = stats.get("recommendation_accuracy", 0)
        if rec_accuracy > 0:
            insights.append(f"Recommendation accuracy: {rec_accuracy}%.")

        return insights

    def identify_knowledge_gaps(self) -> List[Dict[str, Any]]:
        """Identify areas where the system needs more data."""
        outcome_stats = self._get_outcome_stats()
        patterns = self._get_patterns()
        return self._identify_knowledge_gaps(outcome_stats, patterns)

    # ── Internal Helpers ────────────────────────────────────────────────

    def _get_stats(self) -> dict:
        if not self._api_get:
            return {}
        try:
            return self._api_get("/learning/stats")
        except Exception:
            return {}

    def _get_outcome_stats(self) -> list:
        if not self._api_get:
            return []
        try:
            return self._api_get("/learning/outcomes/stats")
        except Exception:
            return []

    def _get_patterns(self) -> list:
        if not self._api_get:
            return []
        try:
            return self._api_get("/learning/patterns")
        except Exception:
            return []

    def _generate_insights(
        self, stats: dict, outcome_stats: list, patterns: list
    ) -> List[str]:
        """Generate insights from stats data."""
        insights = []

        total = stats.get("total_outcomes_tracked", 0)
        if total > 0:
            insights.append(f"Tracked {total} remediation outcomes.")

        success_rate = stats.get("overall_success_rate", 0)
        if success_rate >= 80:
            insights.append("System performance is strong — over 80% success rate.")
        elif success_rate > 0:
            insights.append(f"Success rate is {success_rate}% — learning in progress.")

        # Find improving/declining actions
        for stat in outcome_stats:
            if stat.get("success_rate", 0) < 40 and stat.get("total", 0) >= 3:
                insights.append(
                    f"Action '{stat['action_name']}' has low success ({stat['success_rate']}%) "
                    f"— consider reviewing."
                )

        trending_up = [p for p in patterns if p.get("trending") == "increasing"]
        if trending_up:
            names = [p.get("name", p.get("pattern_type", "")) for p in trending_up[:3]]
            insights.append(f"Trending patterns: {', '.join(names)}.")

        return insights

    def _identify_knowledge_gaps(
        self, outcome_stats: list, patterns: list
    ) -> List[Dict[str, Any]]:
        """Find areas needing more data."""
        gaps = []

        # Actions with low sample size
        for stat in outcome_stats:
            if stat.get("total", 0) < 3:
                gaps.append({
                    "type": "low_sample_size",
                    "action": stat.get("action_name", ""),
                    "current_samples": stat.get("total", 0),
                    "needed": 3,
                    "message": f"'{stat['action_name']}' needs more data points for reliable predictions.",
                })

        # Actions with very low success
        for stat in outcome_stats:
            if stat.get("success_rate", 0) < 30 and stat.get("total", 0) >= 3:
                gaps.append({
                    "type": "low_success_rate",
                    "action": stat.get("action_name", ""),
                    "success_rate": stat.get("success_rate", 0),
                    "message": f"'{stat['action_name']}' has poor performance — may need new approach.",
                })

        return gaps

    def _improvement_recommendations(
        self, outcome_stats: list, gaps: list
    ) -> List[str]:
        """Generate actionable improvement recommendations."""
        recs = []

        low_success = [g for g in gaps if g["type"] == "low_success_rate"]
        if low_success:
            recs.append(
                f"Review {len(low_success)} action(s) with low success rates: "
                + ", ".join(g["action"] for g in low_success)
            )

        low_data = [g for g in gaps if g["type"] == "low_sample_size"]
        if low_data:
            recs.append(
                f"Collect more data for {len(low_data)} action(s) before relying on predictions."
            )

        if not recs:
            recs.append("System is learning well — continue monitoring.")

        return recs
