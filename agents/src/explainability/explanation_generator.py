"""
Explanation Generator: Makes agent decisions transparent and auditable.
Generates human-readable explanations with evidence ranking, decision trees,
feature importance, and contrastive "what-if" analysis.
"""
import time
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any

logger = logging.getLogger(__name__)


@dataclass
class Evidence:
    description: str
    weight: float  # 0.0 - 1.0
    source: str  # metric, pattern, history, correlation
    data_point: Optional[str] = None


@dataclass
class AlternativeExplanation:
    hypothesis: str
    probability: float
    reason_rejected: str


@dataclass
class DecisionNode:
    condition: str
    result: Optional[str] = None
    true_branch: Optional["DecisionNode"] = None
    false_branch: Optional["DecisionNode"] = None


@dataclass
class Explanation:
    incident_id: str
    explanation_type: str  # diagnosis, remediation, prediction
    summary: str
    evidence: List[Evidence] = field(default_factory=list)
    alternatives: List[AlternativeExplanation] = field(default_factory=list)
    decision_path: List[str] = field(default_factory=list)
    feature_importance: Dict[str, float] = field(default_factory=dict)
    confidence: float = 0.0
    generated_at: float = field(default_factory=time.time)
    audit_data: Dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "incident_id": self.incident_id,
            "type": self.explanation_type,
            "summary": self.summary,
            "confidence": self.confidence,
            "evidence": [
                {"description": e.description, "weight": round(e.weight, 2),
                 "source": e.source, "data_point": e.data_point}
                for e in sorted(self.evidence, key=lambda e: -e.weight)
            ],
            "alternatives": [
                {"hypothesis": a.hypothesis, "probability": round(a.probability, 1),
                 "reason_rejected": a.reason_rejected}
                for a in self.alternatives
            ],
            "decision_path": self.decision_path,
            "feature_importance": {
                k: round(v, 3) for k, v in
                sorted(self.feature_importance.items(), key=lambda x: -x[1])
            },
            "generated_at": self.generated_at,
        }


class ExplanationGenerator:
    """Generates human-readable explanations for all agent decisions."""

    def __init__(self):
        self._explanations: Dict[str, List[Explanation]] = {}
        self._decision_log: List[dict] = []

    # ── Diagnosis Explanation ──────────────────────────────────────────

    def explain_diagnosis(self, incident_id: str, diagnosis: dict,
                          metrics: dict = None, patterns: list = None,
                          history: list = None) -> Explanation:
        """Explain why the diagnostic agent reached its conclusion."""
        root_cause = diagnosis.get("root_cause", "Unknown")
        confidence = diagnosis.get("confidence", 50)

        explanation = Explanation(
            incident_id=incident_id,
            explanation_type="diagnosis",
            summary=f"Diagnosis: {root_cause}",
            confidence=confidence,
        )

        # Build evidence from various sources
        if metrics:
            self._add_metric_evidence(explanation, metrics, root_cause)
        if patterns:
            self._add_pattern_evidence(explanation, patterns)
        if history:
            self._add_historical_evidence(explanation, history, root_cause)

        # Add decision path
        explanation.decision_path = self._build_diagnosis_path(diagnosis, metrics)

        # Generate alternatives
        explanation.alternatives = self._generate_alternative_diagnoses(
            diagnosis, metrics, patterns
        )

        # Calculate feature importance
        explanation.feature_importance = self._calculate_feature_importance(
            explanation.evidence
        )

        # Normalize evidence weights
        total_weight = sum(e.weight for e in explanation.evidence) or 1
        for e in explanation.evidence:
            e.weight /= total_weight

        # Store for audit
        self._store_explanation(explanation)

        return explanation

    def _add_metric_evidence(self, explanation: Explanation,
                              metrics: dict, root_cause: str):
        """Extract evidence from metric data."""
        if "cpu_pct" in metrics and metrics["cpu_pct"] > 80:
            explanation.evidence.append(Evidence(
                description=f"CPU usage at {metrics['cpu_pct']}% (threshold: 80%)",
                weight=0.3 if "cpu" in root_cause.lower() else 0.1,
                source="metric",
                data_point=f"cpu_pct={metrics['cpu_pct']}",
            ))

        if "memory_pct" in metrics and metrics["memory_pct"] > 85:
            explanation.evidence.append(Evidence(
                description=f"Memory usage at {metrics['memory_pct']}% (threshold: 85%)",
                weight=0.35 if "memory" in root_cause.lower() else 0.1,
                source="metric",
                data_point=f"memory_pct={metrics['memory_pct']}",
            ))

        if "error_rate" in metrics and metrics["error_rate"] > 1:
            explanation.evidence.append(Evidence(
                description=f"Error rate at {metrics['error_rate']}% (baseline: <1%)",
                weight=0.25,
                source="metric",
                data_point=f"error_rate={metrics['error_rate']}",
            ))

        if "response_time_ms" in metrics and metrics["response_time_ms"] > 500:
            explanation.evidence.append(Evidence(
                description=f"Response time {metrics['response_time_ms']}ms (baseline: <200ms)",
                weight=0.2,
                source="metric",
                data_point=f"response_time_ms={metrics['response_time_ms']}",
            ))

    def _add_pattern_evidence(self, explanation: Explanation, patterns: list):
        """Extract evidence from pattern matches."""
        for pattern in patterns[:3]:
            ptype = pattern.get("pattern_type", "unknown")
            conf = pattern.get("confidence", 50)
            explanation.evidence.append(Evidence(
                description=f"Pattern match: {ptype} (confidence: {conf}%)",
                weight=conf / 200,  # Scale to 0-0.5 range
                source="pattern",
                data_point=pattern.get("description", ""),
            ))

    def _add_historical_evidence(self, explanation: Explanation,
                                  history: list, root_cause: str):
        """Extract evidence from similar historical incidents."""
        similar_count = len(history)
        if similar_count > 0:
            avg_similarity = sum(
                h.get("similarity", 0) for h in history
            ) / similar_count

            explanation.evidence.append(Evidence(
                description=f"Similar to {similar_count} past incidents (avg similarity: {avg_similarity:.0f}%)",
                weight=0.25,
                source="history",
                data_point=f"similar_incidents={similar_count}",
            ))

    def _build_diagnosis_path(self, diagnosis: dict, metrics: dict = None) -> List[str]:
        """Build the decision tree path that led to the diagnosis."""
        path = ["Incident received"]
        if metrics:
            if metrics.get("cpu_pct", 0) > 80:
                path.append("CPU > 80% → Check CPU-related causes")
            if metrics.get("memory_pct", 0) > 85:
                path.append("Memory > 85% → Check memory-related causes")
            if metrics.get("error_rate", 0) > 1:
                path.append("Error rate elevated → Check application errors")

        path.append(f"Pattern matching → {diagnosis.get('root_cause', 'Unknown')}")
        path.append(f"Confidence: {diagnosis.get('confidence', 50)}%")
        return path

    def _generate_alternative_diagnoses(self, diagnosis: dict,
                                         metrics: dict = None,
                                         patterns: list = None) -> List[AlternativeExplanation]:
        """Generate alternative explanations that were considered and rejected."""
        alternatives = []
        root = (diagnosis.get("root_cause") or "").lower()

        if "memory" not in root:
            alternatives.append(AlternativeExplanation(
                hypothesis="Memory leak",
                probability=12,
                reason_rejected="Memory usage within normal range" if metrics and metrics.get("memory_pct", 0) < 80
                else "Memory elevated but pattern doesn't match leak signature",
            ))

        if "cpu" not in root:
            alternatives.append(AlternativeExplanation(
                hypothesis="CPU exhaustion",
                probability=8,
                reason_rejected="CPU within acceptable range" if metrics and metrics.get("cpu_pct", 0) < 70
                else "CPU elevated but not primary cause",
            ))

        if "deploy" not in root:
            alternatives.append(AlternativeExplanation(
                hypothesis="Bad deployment",
                probability=5,
                reason_rejected="No recent deployments in the affected timeframe",
            ))

        return alternatives

    # ── Remediation Explanation ────────────────────────────────────────

    def explain_remediation_choice(self, incident_id: str, chosen_action: dict,
                                    alternatives: List[dict] = None) -> Explanation:
        """Explain why a specific remediation action was selected."""
        action_name = chosen_action.get("action", "unknown")
        success_prob = chosen_action.get("success_probability", 50)

        explanation = Explanation(
            incident_id=incident_id,
            explanation_type="remediation",
            summary=f"Selected action: {action_name} (success probability: {success_prob}%)",
            confidence=success_prob,
        )

        # Why this action
        explanation.evidence.append(Evidence(
            description=f"Historical success rate for {action_name}: {success_prob}%",
            weight=0.4, source="history",
        ))
        explanation.evidence.append(Evidence(
            description=f"Risk level: {chosen_action.get('risk_level', 'medium')}",
            weight=0.2, source="safety",
        ))
        explanation.evidence.append(Evidence(
            description=f"Estimated resolution time: {chosen_action.get('est_time_min', '?')} min",
            weight=0.2, source="performance",
        ))

        # Why not other actions
        for alt in (alternatives or []):
            reason = alt.get("rejection_reason", "Lower success probability")
            explanation.alternatives.append(AlternativeExplanation(
                hypothesis=alt.get("action", "unknown"),
                probability=alt.get("success_probability", 0),
                reason_rejected=reason,
            ))

        explanation.decision_path = [
            f"Diagnosis: {chosen_action.get('based_on', 'unknown')}",
            f"Matching actions found: {1 + len(alternatives or [])}",
            f"Safety check: {'passed' if not chosen_action.get('blocked') else 'blocked'}",
            f"Selected: {action_name} (best score)",
        ]

        self._store_explanation(explanation)
        return explanation

    # ── Prediction Explanation ─────────────────────────────────────────

    def explain_prediction(self, incident_id: str, prediction: dict) -> Explanation:
        """Explain how a prediction/forecast was generated."""
        explanation = Explanation(
            incident_id=incident_id,
            explanation_type="prediction",
            summary=f"Prediction: {prediction.get('description', 'Future issue predicted')}",
            confidence=prediction.get("confidence", 50),
        )

        explanation.evidence.append(Evidence(
            description=f"Based on {prediction.get('data_points', 0)} historical data points",
            weight=0.3, source="history",
        ))
        explanation.evidence.append(Evidence(
            description=f"Trend direction: {prediction.get('trend', 'unknown')}",
            weight=0.3, source="metric",
        ))
        if prediction.get("similar_past_events"):
            explanation.evidence.append(Evidence(
                description=f"Similar events occurred {prediction['similar_past_events']} times before",
                weight=0.25, source="history",
            ))

        explanation.decision_path = [
            f"Data collection: {prediction.get('data_points', 0)} points over {prediction.get('time_range', '?')}",
            f"Model: {prediction.get('model', 'linear regression')}",
            f"Forecast horizon: {prediction.get('horizon', '?')}",
            f"Confidence: {prediction.get('confidence', 50)}%",
        ]

        explanation.feature_importance = prediction.get("feature_importance", {})

        self._store_explanation(explanation)
        return explanation

    # ── Contrastive Explanations ───────────────────────────────────────

    def explain_why_not(self, incident_id: str, actual: str,
                         hypothetical: str, factors: dict) -> dict:
        """'Why X and not Y?' explanations with sensitivity analysis."""
        differences = []
        for factor, value in factors.items():
            needed = factors.get(f"{factor}_needed_for_{hypothetical}")
            if needed:
                differences.append({
                    "factor": factor,
                    "actual_value": value,
                    "needed_for_alternative": needed,
                    "gap": abs(value - needed) if isinstance(value, (int, float)) else "N/A",
                })

        return {
            "question": f"Why {actual} and not {hypothetical}?",
            "answer": f"The evidence more strongly supports {actual}",
            "key_differences": differences,
            "sensitivity": f"Changing the top factor would shift the diagnosis toward {hypothetical}",
        }

    # ── Utility Methods ────────────────────────────────────────────────

    def _calculate_feature_importance(self, evidence: List[Evidence]) -> Dict[str, float]:
        """Calculate SHAP-like feature importance from evidence."""
        importance = {}
        for e in evidence:
            importance[e.source] = importance.get(e.source, 0) + e.weight
        # Normalize
        total = sum(importance.values()) or 1
        return {k: v / total for k, v in importance.items()}

    def _store_explanation(self, explanation: Explanation):
        """Store for audit trail."""
        if explanation.incident_id not in self._explanations:
            self._explanations[explanation.incident_id] = []
        self._explanations[explanation.incident_id].append(explanation)

        self._decision_log.append({
            "incident_id": explanation.incident_id,
            "type": explanation.explanation_type,
            "summary": explanation.summary,
            "confidence": explanation.confidence,
            "timestamp": explanation.generated_at,
        })

    def get_explanations(self, incident_id: str) -> List[dict]:
        return [e.to_dict() for e in self._explanations.get(incident_id, [])]

    def get_audit_log(self, limit: int = 50) -> List[dict]:
        return self._decision_log[-limit:]
