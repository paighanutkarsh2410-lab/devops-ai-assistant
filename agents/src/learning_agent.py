"""
Learning Agent: Learns from every incident to improve diagnosis and remediation.
Pipeline: Fetch incident → Extract patterns → Store in vector DB → Update stats → Recommend.
"""
import sys
import os
import logging
import time
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend', 'src'))

from base_agent import BaseAgent
from config import BACKEND_URL, REDIS_URL
from knowledge_base import QdrantKnowledgeBase, generate_incident_embedding, EmbeddingCache

logger = logging.getLogger(__name__)


class LearningAgent(BaseAgent):
    """Agent that learns from resolved incidents and improves system intelligence."""

    def __init__(self):
        super().__init__("LearningAgent")
        self.kb = QdrantKnowledgeBase()
        self.embedding_cache = EmbeddingCache()
        self._processed_ids = set()
        self._action_stats = {}  # action_name -> {successes, failures, total}

    def tick(self):
        """Process newly resolved incidents and learn from them."""
        try:
            # Fetch resolved incidents
            incidents = self.api_get("/incidents/", {"status": "resolved", "limit": 20})
        except Exception as e:
            print(f"  [LearnAgent] Failed to fetch incidents: {e}")
            return

        learned_count = 0
        for incident in incidents:
            inc_id = incident.get("id")
            if inc_id and inc_id not in self._processed_ids:
                success = self.learn_from_incident(incident)
                if success:
                    learned_count += 1
                self._processed_ids.add(inc_id)

        if learned_count > 0:
            print(f"  [LearnAgent] Learned from {learned_count} new incidents")
        else:
            print(f"  [LearnAgent] No new incidents to learn from")

    # ── Core Learning Pipeline ──────────────────────────────────────────

    def learn_from_incident(self, incident: dict) -> bool:
        """
        Full learning pipeline for a single incident.

        Steps:
          1. Fetch full incident data + actions taken
          2. Extract patterns (symptoms, cause, solution)
          3. Store in vector knowledge base
          4. Update action success statistics
        """
        inc_id = incident.get("id", "")
        print(f"    [LearnAgent] Learning from incident: {incident.get('title', '')[:60]}")

        # Step 1: Gather full data
        actions_taken = self._get_incident_actions(inc_id)
        success = incident.get("auto_resolved", False) or incident.get("status") == "resolved"

        # Step 2: Extract pattern
        pattern = self._extract_pattern(incident, actions_taken)

        # Step 3: Store in knowledge base
        incident_data = {
            "incident_id": str(inc_id),
            "title": incident.get("title", ""),
            "description": incident.get("description", ""),
            "service_name": incident.get("service_name", ""),
            "severity": incident.get("severity", "medium"),
            "root_cause": incident.get("root_cause", ""),
            "solution": incident.get("solution", ""),
            "success": success,
            "resolution_time": incident.get("resolution_time_seconds", 0) or 0,
            "action_taken": pattern.get("action_taken", ""),
            "pattern_type": pattern.get("pattern_type", "unknown"),
            "timestamp": incident.get("resolved_at") or datetime.now(timezone.utc).isoformat(),
        }

        embedding = generate_incident_embedding(incident)
        stored = self.kb.store_incident(incident_data, embedding)

        # Step 4: Update statistics
        if actions_taken:
            for action in actions_taken:
                action_name = action.get("action_name", "")
                action_success = action.get("status") == "success"
                if action_name:
                    self._update_action_stats(action_name, action_success)
                    self._record_outcome(inc_id, action, pattern.get("pattern_type", ""))

        # Step 5: Update learning data in backend
        self._update_learning_data(pattern, success)

        if stored:
            logger.info(f"Learned from incident {inc_id}: pattern={pattern.get('pattern_type')}")
        return stored

    # ── Similarity Search ───────────────────────────────────────────────

    def get_similar_incidents(
        self, incident: dict, top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find similar past incidents from the knowledge base.

        Returns list of similar incidents with scores and success rates.
        """
        embedding = generate_incident_embedding(incident)
        similar = self.kb.search_similar(
            query_embedding=embedding,
            top_k=top_k,
            min_score=0.65,
            service_filter=None,
        )

        # Enrich with action success rates
        for item in similar:
            action = item.get("action_taken", "")
            if action and action in self._action_stats:
                stats = self._action_stats[action]
                item["action_success_rate"] = (
                    stats["successes"] / stats["total"] if stats["total"] > 0 else 0
                )
            else:
                item["action_success_rate"] = 0

        return similar

    def get_best_action_for_incident(self, incident: dict) -> Optional[Dict[str, Any]]:
        """
        Recommend the best action based on similar past incidents.

        Returns:
            Dict with action_name, confidence, success_rate, similar_count
        """
        similar = self.get_similar_incidents(incident, top_k=10)
        if not similar:
            return None

        # Tally actions from similar incidents
        action_scores = {}
        for item in similar:
            action = item.get("action_taken", "")
            if not action:
                continue

            score = item.get("score", 0)
            success = item.get("success", False)

            if action not in action_scores:
                action_scores[action] = {
                    "total": 0, "successes": 0,
                    "score_sum": 0.0, "count": 0,
                }

            action_scores[action]["total"] += 1
            action_scores[action]["score_sum"] += score
            action_scores[action]["count"] += 1
            if success:
                action_scores[action]["successes"] += 1

        if not action_scores:
            return None

        # Rank: score = avg_similarity * success_rate * frequency_bonus
        best_action = None
        best_score = -1

        for action, stats in action_scores.items():
            avg_sim = stats["score_sum"] / stats["count"]
            success_rate = stats["successes"] / stats["total"] if stats["total"] > 0 else 0
            freq_bonus = min(stats["count"] / 5, 1.0)  # caps at 5 occurrences
            combined = avg_sim * success_rate * (0.7 + 0.3 * freq_bonus)

            if combined > best_score:
                best_score = combined
                best_action = {
                    "action_name": action,
                    "confidence": round(combined * 100, 1),
                    "success_rate": round(success_rate * 100, 1),
                    "similar_count": stats["total"],
                    "avg_similarity": round(avg_sim, 3),
                }

        return best_action

    # ── Action Statistics ───────────────────────────────────────────────

    def update_action_success_rate(self, action_name: str, success: bool):
        """Track which actions work (public API for other agents)."""
        self._update_action_stats(action_name, success)

    def get_action_stats(self) -> Dict[str, Dict]:
        """Return success rate stats for all tracked actions."""
        result = {}
        for action, stats in self._action_stats.items():
            total = stats["total"]
            result[action] = {
                "total": total,
                "successes": stats["successes"],
                "failures": stats["failures"],
                "success_rate": round(stats["successes"] / total * 100, 1) if total > 0 else 0,
            }
        return result

    # ── Pattern Analysis ────────────────────────────────────────────────

    def analyze_patterns(self) -> Dict[str, Any]:
        """
        Run periodic pattern analysis. Identifies common incident types,
        finds correlations, and generates insights.
        """
        stats = self.kb.get_collection_stats()
        action_stats = self.get_action_stats()

        # Find most effective actions
        best_actions = sorted(
            action_stats.items(),
            key=lambda x: x[1]["success_rate"],
            reverse=True,
        )[:5]

        # Find most common patterns from stored learning data
        try:
            learning_data = self.api_get("/learning/data", {"limit": 50})
        except Exception:
            learning_data = []

        pattern_summary = {}
        for entry in learning_data:
            pt = entry.get("pattern_type", "unknown")
            if pt not in pattern_summary:
                pattern_summary[pt] = {"count": 0, "avg_success_rate": 0, "total_rate": 0}
            pattern_summary[pt]["count"] += entry.get("frequency", 1)
            pattern_summary[pt]["total_rate"] += entry.get("success_rate", 0)

        for pt in pattern_summary:
            count = pattern_summary[pt]["count"]
            if count > 0:
                pattern_summary[pt]["avg_success_rate"] = round(
                    pattern_summary[pt]["total_rate"] / count, 1
                )

        return {
            "knowledge_base": stats,
            "action_effectiveness": dict(best_actions),
            "pattern_summary": pattern_summary,
            "total_actions_tracked": sum(s["total"] for s in action_stats.values()),
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
        }

    # ── Internal Helpers ────────────────────────────────────────────────

    def _extract_pattern(self, incident: dict, actions: list) -> dict:
        """Extract a pattern classification from the incident."""
        root_cause = (incident.get("root_cause", "") or "").lower()
        title = (incident.get("title", "") or "").lower()
        text = f"{root_cause} {title}"

        # Classify pattern type
        pattern_map = {
            "memory_leak": ["memory", "oom", "out of memory", "heap", "leak"],
            "cpu_spike": ["cpu", "high cpu", "processor", "compute"],
            "api_timeout": ["timeout", "latency", "slow", "response time"],
            "disk_full": ["disk", "storage", "space", "inode"],
            "database_slow": ["database", "query", "connection pool", "deadlock"],
            "deployment_issue": ["deploy", "rollback", "version", "release"],
            "cache_issue": ["cache", "redis", "stale", "miss"],
            "network_issue": ["network", "dns", "connection refused", "socket"],
            "process_stuck": ["stuck", "zombie", "hung", "unresponsive"],
        }

        pattern_type = "unknown"
        for ptype, keywords in pattern_map.items():
            if any(kw in text for kw in keywords):
                pattern_type = ptype
                break

        action_taken = ""
        if actions:
            # Use the most recent successful action
            for a in sorted(actions, key=lambda x: x.get("executed_at", ""), reverse=True):
                if a.get("status") == "success":
                    action_taken = a.get("action_name", "")
                    break
            if not action_taken and actions:
                action_taken = actions[0].get("action_name", "")

        return {
            "pattern_type": pattern_type,
            "action_taken": action_taken,
            "symptoms": {
                "root_cause_keywords": [w for w in root_cause.split() if len(w) > 3][:10],
                "severity": incident.get("severity", ""),
                "service": incident.get("service_name", ""),
            },
        }

    def _get_incident_actions(self, incident_id: str) -> list:
        """Fetch remediation actions taken for an incident."""
        try:
            return self.api_get(f"/audit/incidents/{incident_id}/actions")
        except Exception:
            return []

    def _update_action_stats(self, action_name: str, success: bool):
        """Update in-memory action statistics."""
        if action_name not in self._action_stats:
            self._action_stats[action_name] = {"successes": 0, "failures": 0, "total": 0}

        stats = self._action_stats[action_name]
        stats["total"] += 1
        if success:
            stats["successes"] += 1
        else:
            stats["failures"] += 1

    def _record_outcome(self, incident_id: str, action: dict, pattern_type: str):
        """Record action outcome in the backend."""
        try:
            self.api_post("/learning/outcomes", {
                "incident_id": str(incident_id),
                "action_name": action.get("action_name", ""),
                "incident_pattern": pattern_type,
                "service_name": action.get("service_name", ""),
                "success": action.get("status") == "success",
                "duration_seconds": action.get("duration_seconds", 0),
                "impact_score": action.get("impact_score", 0),
            })
        except Exception as e:
            logger.debug(f"Failed to record outcome: {e}")

    def _update_learning_data(self, pattern: dict, success: bool):
        """Update or create learning data entry in the backend."""
        try:
            self.api_post("/learning/data", {
                "pattern_type": pattern.get("pattern_type", "unknown"),
                "action_name": pattern.get("action_taken", ""),
                "success": success,
                "symptoms": pattern.get("symptoms"),
            })
        except Exception as e:
            logger.debug(f"Failed to update learning data: {e}")
