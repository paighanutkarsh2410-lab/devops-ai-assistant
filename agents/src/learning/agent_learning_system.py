"""
Agent Learning System: Tracks agent performance, learns from successes/failures,
provides A/B testing, and continuously improves agent strategies.
"""
import time
import math
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class LearningRecord:
    agent_id: str
    task_type: str
    incident_type: str
    service: str
    strategy: str
    success: bool
    confidence: float
    duration_ms: float
    timestamp: float = field(default_factory=time.time)
    outcome_details: Dict = field(default_factory=dict)


@dataclass
class StrategyStats:
    strategy: str
    total_attempts: int = 0
    successes: int = 0
    failures: int = 0
    avg_confidence: float = 0.0
    avg_duration_ms: float = 0.0
    success_rate: float = 0.0
    elo_score: float = 1000.0  # ELO rating for A/B testing


class AgentLearningSystem:
    """Tracks and improves agent performance over time."""

    def __init__(self):
        self._records: List[LearningRecord] = []
        self._strategy_stats: Dict[str, Dict[str, StrategyStats]] = defaultdict(dict)
        # key: (agent_id, task_type) → {strategy_name: StrategyStats}
        self._agent_accuracy: Dict[str, List[bool]] = defaultdict(list)
        self._thresholds: Dict[str, Dict[str, float]] = defaultdict(dict)
        # Per-service detection thresholds
        self._ab_experiments: Dict[str, Dict] = {}

    # ── Learn from Outcomes ────────────────────────────────────────────

    def learn_from_success(self, agent_id: str, task_type: str,
                           incident_type: str, service: str,
                           strategy: str, confidence: float,
                           duration_ms: float, details: dict = None):
        """Record and learn from a successful agent action."""
        record = LearningRecord(
            agent_id=agent_id, task_type=task_type,
            incident_type=incident_type, service=service,
            strategy=strategy, success=True,
            confidence=confidence, duration_ms=duration_ms,
            outcome_details=details or {},
        )
        self._records.append(record)
        self._agent_accuracy[agent_id].append(True)

        key = f"{agent_id}:{task_type}"
        stats = self._get_or_create_stats(key, strategy)
        stats.total_attempts += 1
        stats.successes += 1
        self._update_stats(stats, confidence, duration_ms)

        # Boost confidence in this strategy
        stats.elo_score += 10

        logger.info(f"[Learning] Success: {agent_id}/{task_type} using '{strategy}' "
                     f"(rate: {stats.success_rate:.0f}%, ELO: {stats.elo_score:.0f})")

    def learn_from_failure(self, agent_id: str, task_type: str,
                           incident_type: str, service: str,
                           strategy: str, confidence: float,
                           duration_ms: float, details: dict = None):
        """Record failure and adjust strategy weights."""
        record = LearningRecord(
            agent_id=agent_id, task_type=task_type,
            incident_type=incident_type, service=service,
            strategy=strategy, success=False,
            confidence=confidence, duration_ms=duration_ms,
            outcome_details=details or {},
        )
        self._records.append(record)
        self._agent_accuracy[agent_id].append(False)

        key = f"{agent_id}:{task_type}"
        stats = self._get_or_create_stats(key, strategy)
        stats.total_attempts += 1
        stats.failures += 1
        self._update_stats(stats, confidence, duration_ms)

        # Penalize this strategy
        stats.elo_score = max(100, stats.elo_score - 15)

        # Record failure pattern for avoidance
        failure_key = f"{incident_type}:{service}"
        if failure_key not in self._thresholds:
            self._thresholds[failure_key] = {}
        self._thresholds[failure_key][strategy] = stats.success_rate

        logger.info(f"[Learning] Failure: {agent_id}/{task_type} using '{strategy}' "
                     f"(rate: {stats.success_rate:.0f}%, ELO: {stats.elo_score:.0f})")

    def _get_or_create_stats(self, key: str, strategy: str) -> StrategyStats:
        if strategy not in self._strategy_stats[key]:
            self._strategy_stats[key][strategy] = StrategyStats(strategy=strategy)
        return self._strategy_stats[key][strategy]

    def _update_stats(self, stats: StrategyStats, confidence: float, duration_ms: float):
        n = stats.total_attempts
        stats.avg_confidence = (stats.avg_confidence * (n - 1) + confidence) / n
        stats.avg_duration_ms = (stats.avg_duration_ms * (n - 1) + duration_ms) / n
        stats.success_rate = (stats.successes / n) * 100

    # ── Strategy Selection ─────────────────────────────────────────────

    def get_best_strategy(self, agent_id: str, task_type: str,
                          min_attempts: int = 3) -> Optional[str]:
        """Get the best strategy based on learning history."""
        key = f"{agent_id}:{task_type}"
        strategies = self._strategy_stats.get(key, {})

        if not strategies:
            return None

        # Filter strategies with enough data
        candidates = [
            s for s in strategies.values()
            if s.total_attempts >= min_attempts
        ]

        if not candidates:
            return None

        # Score: weighted combination of success rate, speed, and ELO
        def score(s: StrategyStats) -> float:
            rate_score = s.success_rate / 100
            speed_score = 1.0 / (1 + s.avg_duration_ms / 1000)
            elo_score = s.elo_score / 2000
            return rate_score * 0.5 + speed_score * 0.2 + elo_score * 0.3

        best = max(candidates, key=score)
        return best.strategy

    def get_strategy_ranking(self, agent_id: str, task_type: str) -> List[dict]:
        """Rank all strategies for a given agent/task combination."""
        key = f"{agent_id}:{task_type}"
        strategies = self._strategy_stats.get(key, {})

        ranking = []
        for name, stats in strategies.items():
            ranking.append({
                "strategy": name,
                "success_rate": round(stats.success_rate, 1),
                "attempts": stats.total_attempts,
                "avg_duration_ms": round(stats.avg_duration_ms, 1),
                "elo_score": round(stats.elo_score, 0),
                "avg_confidence": round(stats.avg_confidence, 1),
            })

        ranking.sort(key=lambda x: (-x["success_rate"], x["avg_duration_ms"]))
        return ranking

    # ── A/B Testing ────────────────────────────────────────────────────

    def create_ab_experiment(self, experiment_id: str, agent_id: str,
                             task_type: str, strategies: List[str],
                             traffic_split: List[float] = None) -> dict:
        """Create an A/B test between strategies."""
        n = len(strategies)
        split = traffic_split or [1.0 / n] * n

        self._ab_experiments[experiment_id] = {
            "agent_id": agent_id,
            "task_type": task_type,
            "strategies": strategies,
            "traffic_split": split,
            "results": {s: {"attempts": 0, "successes": 0} for s in strategies},
            "created_at": time.time(),
            "status": "running",
        }
        return self._ab_experiments[experiment_id]

    def get_ab_assignment(self, experiment_id: str) -> Optional[str]:
        """Get which strategy to use based on traffic split."""
        exp = self._ab_experiments.get(experiment_id)
        if not exp or exp["status"] != "running":
            return None

        import random
        r = random.random()
        cumulative = 0
        for strategy, weight in zip(exp["strategies"], exp["traffic_split"]):
            cumulative += weight
            if r <= cumulative:
                return strategy
        return exp["strategies"][-1]

    def record_ab_result(self, experiment_id: str, strategy: str, success: bool):
        exp = self._ab_experiments.get(experiment_id)
        if not exp:
            return
        if strategy in exp["results"]:
            exp["results"][strategy]["attempts"] += 1
            if success:
                exp["results"][strategy]["successes"] += 1

    def evaluate_ab_experiment(self, experiment_id: str) -> dict:
        """Evaluate A/B experiment with statistical significance."""
        exp = self._ab_experiments.get(experiment_id)
        if not exp:
            return {"error": "Experiment not found"}

        results = {}
        for strategy, data in exp["results"].items():
            n = data["attempts"]
            s = data["successes"]
            rate = (s / n * 100) if n > 0 else 0
            # Wilson confidence interval
            if n > 0:
                z = 1.96  # 95% confidence
                p = s / n
                denom = 1 + z * z / n
                center = (p + z * z / (2 * n)) / denom
                margin = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n) / denom
                ci_low = max(0, (center - margin) * 100)
                ci_high = min(100, (center + margin) * 100)
            else:
                ci_low, ci_high = 0, 100

            results[strategy] = {
                "attempts": n, "successes": s,
                "success_rate": round(rate, 1),
                "ci_95_low": round(ci_low, 1),
                "ci_95_high": round(ci_high, 1),
            }

        # Determine winner
        strategies_by_rate = sorted(results.items(), key=lambda x: -x[1]["success_rate"])
        winner = strategies_by_rate[0][0] if strategies_by_rate else None

        # Check if statistically significant (non-overlapping CIs)
        significant = False
        if len(strategies_by_rate) >= 2:
            best = strategies_by_rate[0][1]
            second = strategies_by_rate[1][1]
            significant = best["ci_95_low"] > second["ci_95_high"]

        return {
            "experiment_id": experiment_id,
            "results": results,
            "winner": winner,
            "statistically_significant": significant,
            "total_samples": sum(r["attempts"] for r in results.values()),
        }

    # ── Feedback Tracking ──────────────────────────────────────────────

    def get_agent_accuracy(self, agent_id: str, window: int = 100) -> dict:
        """Get accuracy metrics for an agent over recent tasks."""
        history = self._agent_accuracy.get(agent_id, [])
        recent = history[-window:] if len(history) > window else history

        total = len(recent)
        correct = sum(1 for r in recent if r)
        accuracy = (correct / total * 100) if total > 0 else 0

        # Trend: compare first half vs second half
        if total >= 10:
            mid = total // 2
            first_half = sum(1 for r in recent[:mid] if r) / mid * 100
            second_half = sum(1 for r in recent[mid:] if r) / (total - mid) * 100
            trend = "improving" if second_half > first_half + 2 else (
                "declining" if second_half < first_half - 2 else "stable"
            )
        else:
            trend = "insufficient_data"

        return {
            "agent_id": agent_id,
            "accuracy": round(accuracy, 1),
            "total_tasks": total,
            "correct": correct,
            "trend": trend,
            "window": window,
        }

    # ── Progress Dashboard ─────────────────────────────────────────────

    def get_learning_progress(self) -> dict:
        """Dashboard data showing agent improvement over time."""
        agent_stats = {}
        for agent_id, history in self._agent_accuracy.items():
            agent_stats[agent_id] = self.get_agent_accuracy(agent_id)

        # Strategy diversity
        total_strategies = sum(
            len(strategies) for strategies in self._strategy_stats.values()
        )

        # Active experiments
        active_experiments = sum(
            1 for e in self._ab_experiments.values() if e["status"] == "running"
        )

        return {
            "total_records": len(self._records),
            "agents": agent_stats,
            "total_strategies_tracked": total_strategies,
            "active_experiments": active_experiments,
            "experiments": {
                eid: self.evaluate_ab_experiment(eid)
                for eid in self._ab_experiments
            },
        }
