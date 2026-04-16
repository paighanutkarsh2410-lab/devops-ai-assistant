"""
Base class for all specialist agents. Provides common analysis framework,
inter-agent collaboration, and result formatting.
"""
import time
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class Finding:
    category: str
    severity: str  # critical, high, medium, low, info
    title: str
    description: str
    evidence: List[str] = field(default_factory=list)
    recommendation: str = ""
    confidence: float = 80.0


@dataclass
class SpecialistReport:
    agent_id: str
    agent_type: str
    incident_id: str
    findings: List[Finding] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    metrics_analyzed: Dict = field(default_factory=dict)
    confidence: float = 0.0
    analysis_time_ms: float = 0.0
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "incident_id": self.incident_id,
            "findings": [
                {
                    "category": f.category, "severity": f.severity,
                    "title": f.title, "description": f.description,
                    "evidence": f.evidence, "recommendation": f.recommendation,
                    "confidence": f.confidence,
                }
                for f in self.findings
            ],
            "recommendations": self.recommendations,
            "metrics_analyzed": self.metrics_analyzed,
            "confidence": self.confidence,
            "analysis_time_ms": round(self.analysis_time_ms, 1),
            "error": self.error,
        }


class BaseSpecialist:
    """Base class for domain-specialist agents."""

    AGENT_TYPE = "specialist"
    DOMAINS: List[str] = []
    ACTIONS: List[str] = ["investigate", "diagnose"]

    def __init__(self, agent_id: str = None):
        self.agent_id = agent_id or f"{self.AGENT_TYPE}-specialist"
        self._collaborators: Dict[str, "BaseSpecialist"] = {}

    def analyze(self, incident: dict, context: dict = None) -> SpecialistReport:
        """Run full analysis. Subclasses implement _perform_analysis."""
        start = time.time()
        report = SpecialistReport(
            agent_id=self.agent_id,
            agent_type=self.AGENT_TYPE,
            incident_id=incident.get("id", "unknown"),
        )
        try:
            self._perform_analysis(incident, context or {}, report)
            if report.findings:
                report.confidence = sum(f.confidence for f in report.findings) / len(report.findings)
            report.recommendations = list(dict.fromkeys(
                [f.recommendation for f in report.findings if f.recommendation] + report.recommendations
            ))
        except Exception as e:
            report.error = str(e)
            logger.error(f"[{self.agent_id}] Analysis error: {e}")
        report.analysis_time_ms = (time.time() - start) * 1000
        return report

    def _perform_analysis(self, incident: dict, context: dict, report: SpecialistReport):
        raise NotImplementedError

    def register_collaborator(self, name: str, agent: "BaseSpecialist"):
        self._collaborators[name] = agent

    def consult(self, collaborator_name: str, incident: dict, context: dict = None) -> Optional[SpecialistReport]:
        agent = self._collaborators.get(collaborator_name)
        if agent:
            logger.info(f"[{self.agent_id}] Consulting {collaborator_name}")
            return agent.analyze(incident, context)
        return None
