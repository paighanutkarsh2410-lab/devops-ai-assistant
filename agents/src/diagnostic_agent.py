"""
Diagnostic Agent: Investigates incidents using AI to find root causes.
Uses Claude API for analysis, correlation engine for context, and knowledge base for history.
"""
import sys
import os
import json
import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend', 'src'))

from base_agent import BaseAgent
from correlation_engine import CorrelationEngine
from knowledge_base import KnowledgeBase
from config import BACKEND_URL, ANTHROPIC_API_KEY


class DiagnosticAgent(BaseAgent):
    def __init__(self):
        super().__init__("DiagnosticAgent")
        self.correlation_engine = CorrelationEngine(self.api_get)
        self.knowledge_base = KnowledgeBase()
        self._processed_ids = set()

    def tick(self):
        """Check for new undiagnosed incidents and analyze them."""
        try:
            incidents = self.api_get("/incidents/", {"status": "open", "limit": 10})
        except Exception as e:
            print(f"  [DiagAgent] Failed to fetch incidents: {e}")
            return

        for incident in incidents:
            inc_id = incident.get("id")
            if inc_id not in self._processed_ids:
                print(f"\n  [DiagAgent] Analyzing incident: {incident.get('title')}")
                self.analyze_incident(incident)
                self._processed_ids.add(inc_id)

        if not incidents:
            print(f"  [DiagAgent] No open incidents to analyze")

    def analyze_incident(self, incident: dict):
        """Full diagnostic analysis pipeline."""
        inc_id = incident.get("id")
        service = incident.get("service_name", "")

        # Step 1: Gather Context
        print(f"    Step 1: Gathering context...")
        context = self._gather_context(incident)

        # Step 2: Check Knowledge Base
        print(f"    Step 2: Searching knowledge base...")
        similar = self.knowledge_base.search_similar(
            incident.get("title", ""),
            incident.get("description", ""),
            service
        )
        if similar and similar[0]["score"] > 0.8:
            print(f"    Found high-confidence match: {similar[0]['title']} (score: {similar[0]['score']:.2f})")

        # Step 3: Run Correlation Engine
        print(f"    Step 3: Running correlation engine...")
        correlations = self.correlation_engine.correlate_incident(incident)
        print(f"    Correlations: {correlations.get('likely_cause', 'none')}")

        # Step 4: AI Analysis
        print(f"    Step 4: Running AI analysis...")
        analysis = self._run_ai_analysis(incident, context, similar, correlations)

        # Step 5: Update Incident
        print(f"    Step 5: Updating incident with findings...")
        self._update_incident(inc_id, analysis)

        # Step 6: Store in knowledge base for future reference
        incident["root_cause"] = analysis.get("root_cause", "")
        incident["solution"] = "; ".join(analysis.get("recommended_actions", []))
        self.knowledge_base.store_incident(incident)

        print(f"    Diagnosis complete:")
        print(f"      Root cause: {analysis.get('root_cause', 'Unknown')}")
        print(f"      Confidence: {analysis.get('confidence', 0)}%")
        print(f"      Actions: {analysis.get('recommended_actions', [])}")

    def _gather_context(self, incident: dict) -> dict:
        """Gather all contextual data for analysis."""
        service = incident.get("service_name", "")
        context = {"metrics": [], "logs": [], "deployments": []}

        # Recent metrics
        try:
            context["metrics"] = self.api_get("/metrics/", {
                "service_name": service, "hours": 1, "limit": 30
            })
        except Exception:
            pass

        # Recent logs
        try:
            context["logs"] = self.api_get("/logs/errors", {
                "service_name": service, "hours": 1
            })
        except Exception:
            pass

        # Recent deployments
        try:
            context["deployments"] = self.api_get("/deployments/recent", {"hours": 24})
        except Exception:
            pass

        print(f"      Metrics: {len(context['metrics'])}, Logs: {len(context['logs'])}, "
              f"Deployments: {len(context['deployments'])}")
        return context

    def _run_ai_analysis(self, incident: dict, context: dict,
                         similar: list, correlations: dict) -> dict:
        """Call Claude API for incident analysis."""
        # If knowledge base has high-confidence match, use that
        if similar and similar[0]["score"] > 0.8:
            return {
                "root_cause": similar[0]["root_cause"],
                "confidence": int(similar[0]["score"] * 100),
                "reasoning": f"Matched similar past incident: {similar[0]['title']}",
                "recommended_actions": [similar[0].get("solution", "Review past resolution")],
                "severity_assessment": incident.get("severity", "medium"),
                "similar_pattern": similar[0]["title"],
            }

        # Call Claude API via backend service
        try:
            from services.llm_service import analyze_incident
            analysis = analyze_incident(
                incident=incident,
                metrics=context.get("metrics", []),
                logs=context.get("logs", []),
                deployments=context.get("deployments", []),
                similar_incidents=similar
            )
            return analysis
        except Exception as e:
            print(f"      [WARN] AI analysis failed: {e}")
            return self._fallback_analysis(incident, context, correlations)

    def _fallback_analysis(self, incident: dict, context: dict, correlations: dict) -> dict:
        """Rule-based fallback when AI analysis fails."""
        cause = correlations.get("likely_cause", "Unable to determine")
        return {
            "root_cause": cause,
            "confidence": min(correlations.get("max_score", 30), 60),
            "reasoning": "Rule-based analysis (AI unavailable)",
            "recommended_actions": ["Check service logs", "Review recent deployments", "Monitor metrics"],
            "severity_assessment": incident.get("severity", "medium"),
            "similar_pattern": "N/A"
        }

    def _update_incident(self, incident_id: str, analysis: dict):
        """Update the incident with diagnostic findings."""
        try:
            update_data = {
                "root_cause": analysis.get("root_cause", "Under investigation"),
                "solution": "; ".join(analysis.get("recommended_actions", [])),
                "status": "investigating"
            }
            self.api_post(f"/incidents/{incident_id}", update_data)
        except Exception:
            # Use PATCH via requests directly
            try:
                headers = self._headers()
                requests.patch(
                    f"{BACKEND_URL}/incidents/{incident_id}",
                    headers=headers,
                    json={
                        "root_cause": analysis.get("root_cause", "Under investigation"),
                        "solution": "; ".join(analysis.get("recommended_actions", [])),
                        "status": "investigating"
                    },
                    timeout=10
                )
            except Exception as e:
                print(f"      [WARN] Failed to update incident: {e}")
