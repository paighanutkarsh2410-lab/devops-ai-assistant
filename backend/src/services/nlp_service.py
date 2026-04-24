"""
Natural Language Query Handler.
Parses user questions, queries the database, and uses Claude
to generate conversational answers about system state.
"""
import os
import re
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from models.incident import Incident
from models.metric import Metric
from models.alert import Alert

logger = logging.getLogger(__name__)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

try:
    import anthropic
    LLM_AVAILABLE = bool(ANTHROPIC_API_KEY)
except ImportError:
    LLM_AVAILABLE = False


# Intent classification patterns
INTENT_PATTERNS = {
    "current_status": [
        r"status.*(?:of|for)\s+(\S+)",
        r"how\s+is\s+(\S+)",
        r"what.*happening.*(?:with|on)\s+(\S+)",
        r"health.*(?:of|for)\s+(\S+)",
        r"system\s+status",
    ],
    "incident_query": [
        r"show.*incidents",
        r"list.*incidents",
        r"incidents.*(?:last|this|past)\s+(\w+)",
        r"what.*incidents",
        r"recent.*incidents",
    ],
    "diagnostic": [
        r"why\s+is\s+(.+?)(?:\s+slow|\s+down|\s+failing|\?)",
        r"what.*(?:wrong|issue|problem).*(?:with|on)\s+(\S+)",
        r"diagnos(?:e|is)",
        r"root\s+cause",
    ],
    "prediction": [
        r"predict.*(?:when|if)",
        r"forecast",
        r"(?:will|when).*(?:run out|full|exhaust|breach)",
        r"capacity",
        r"cost.*(?:forecast|predict|next month)",
    ],
    "metrics": [
        r"(?:show|get|what).*(?:cpu|memory|disk|metrics?).*(?:for|of|on)\s+(\S+)",
        r"metrics\s+(?:for|of)\s+(\S+)",
        r"current.*(?:cpu|memory|disk)",
    ],
    "summary": [
        r"summary",
        r"overview",
        r"how.*(?:system|things|everything).*doing",
        r"report",
    ],
}


class NLPQueryHandler:
    """Handles natural language queries about the DevOps system."""

    def __init__(self, db: Session = None):
        self._db = db
        self._conversation_history: List[dict] = []
        if LLM_AVAILABLE:
            self._client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        else:
            self._client = None

    def set_db(self, db: Session):
        """Set the database session."""
        self._db = db

    # ── Main Query Entry Point ─────────────────────────────────────────

    def query(self, user_question: str) -> Dict[str, Any]:
        """
        Process a natural language question and return an answer.

        Args:
            user_question: The user's question in plain English.

        Returns:
            Dict with answer, data, intent, sources.
        """
        # 1. Parse intent
        intent = self.parse_query(user_question)

        # 2. Execute query to get data
        data = self.execute_query(intent)

        # 3. Generate natural language response
        answer = self.generate_response(user_question, data, intent)

        # 4. Track conversation
        self._conversation_history.append({
            "role": "user",
            "content": user_question,
        })
        self._conversation_history.append({
            "role": "assistant",
            "content": answer,
        })

        # Keep last 20 messages
        if len(self._conversation_history) > 20:
            self._conversation_history = self._conversation_history[-20:]

        return {
            "answer": answer,
            "intent": intent,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }

    # ── Intent Parsing ─────────────────────────────────────────────────

    def parse_query(self, question: str) -> Dict[str, Any]:
        """
        Parse user question to determine intent and extract entities.

        Returns:
            Dict with intent_type, entities (service, timeframe, etc.).
        """
        question_lower = question.lower().strip()
        entities = {}

        for intent_type, patterns in INTENT_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, question_lower)
                if match:
                    groups = match.groups()
                    if groups:
                        entities["service"] = groups[0].strip("?.,! ")
                    return {
                        "intent_type": intent_type,
                        "entities": entities,
                        "raw_question": question,
                    }

        # Fallback: try Claude to classify intent
        return {
            "intent_type": "general",
            "entities": entities,
            "raw_question": question,
        }

    # ── Data Retrieval ─────────────────────────────────────────────────

    def execute_query(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute database queries based on parsed intent.

        Returns:
            Dict with relevant data for the response.
        """
        intent_type = intent.get("intent_type", "general")
        entities = intent.get("entities", {})
        service = entities.get("service")

        if not self._db:
            return {"error": "Database not available"}

        try:
            if intent_type == "current_status":
                return self._get_service_status(service)
            elif intent_type == "incident_query":
                return self._get_incidents(entities)
            elif intent_type == "diagnostic":
                return self._get_diagnostic_info(service)
            elif intent_type == "prediction":
                return self._get_predictions()
            elif intent_type == "metrics":
                return self._get_metrics(service)
            elif intent_type == "summary":
                return self._get_system_summary()
            else:
                return self._get_system_summary()
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return {"error": str(e)}

    def _get_service_status(self, service: str = None) -> dict:
        """Get current status of a service or all services."""
        data = {"type": "service_status"}

        # Recent incidents
        query = self._db.query(Incident).filter(
            Incident.status != "resolved"
        )
        if service:
            query = query.filter(Incident.service_name.ilike(f"%{service}%"))

        open_incidents = query.order_by(desc(Incident.detected_at)).limit(10).all()
        data["open_incidents"] = [
            {
                "id": str(i.id),
                "title": i.title,
                "severity": i.severity,
                "service": i.service_name,
                "status": i.status,
                "detected_at": i.detected_at.isoformat() if i.detected_at else None,
            }
            for i in open_incidents
        ]

        # Recent metrics
        metric_query = self._db.query(Metric)
        if service:
            metric_query = metric_query.filter(Metric.service_name.ilike(f"%{service}%"))

        recent_metrics = metric_query.order_by(desc(Metric.recorded_at)).limit(20).all()
        metrics_by_name = {}
        for m in recent_metrics:
            key = f"{m.service_name}:{m.metric_name}"
            if key not in metrics_by_name:
                metrics_by_name[key] = {
                    "service": m.service_name,
                    "metric": m.metric_name,
                    "value": m.value,
                    "unit": m.unit,
                    "recorded_at": m.recorded_at.isoformat() if m.recorded_at else None,
                }

        data["metrics"] = list(metrics_by_name.values())
        data["service_filter"] = service
        return data

    def _get_incidents(self, entities: dict) -> dict:
        """Get incidents matching criteria."""
        query = self._db.query(Incident).order_by(desc(Incident.detected_at))

        service = entities.get("service")
        if service:
            query = query.filter(Incident.service_name.ilike(f"%{service}%"))

        incidents = query.limit(20).all()
        return {
            "type": "incidents",
            "count": len(incidents),
            "incidents": [
                {
                    "id": str(i.id),
                    "title": i.title,
                    "severity": i.severity,
                    "service": i.service_name,
                    "status": i.status,
                    "root_cause": i.root_cause,
                    "detected_at": i.detected_at.isoformat() if i.detected_at else None,
                }
                for i in incidents
            ],
        }

    def _get_diagnostic_info(self, service: str = None) -> dict:
        """Get diagnostic information for a service."""
        query = self._db.query(Incident).filter(
            Incident.status != "resolved"
        )
        if service:
            query = query.filter(Incident.service_name.ilike(f"%{service}%"))

        incidents = query.order_by(desc(Incident.detected_at)).limit(5).all()

        return {
            "type": "diagnostic",
            "service": service,
            "active_incidents": [
                {
                    "title": i.title,
                    "severity": i.severity,
                    "root_cause": i.root_cause or "Under investigation",
                    "status": i.status,
                }
                for i in incidents
            ],
        }

    def _get_predictions(self) -> dict:
        """Get prediction and forecast data."""
        try:
            from models.predictive_alert import PredictiveAlert
            alerts = self._db.query(PredictiveAlert).filter(
                PredictiveAlert.prevented == False
            ).order_by(desc(PredictiveAlert.created_at)).limit(10).all()

            return {
                "type": "predictions",
                "active_predictions": [
                    {
                        "title": a.title,
                        "severity": a.severity,
                        "type": a.prediction_type,
                        "service": a.service_name,
                        "confidence": a.confidence,
                        "hours_until": a.hours_until_issue,
                    }
                    for a in alerts
                ],
            }
        except Exception:
            return {"type": "predictions", "active_predictions": []}

    def _get_metrics(self, service: str = None) -> dict:
        """Get current metrics for a service."""
        query = self._db.query(Metric)
        if service:
            query = query.filter(Metric.service_name.ilike(f"%{service}%"))

        metrics = query.order_by(desc(Metric.recorded_at)).limit(50).all()

        by_service = {}
        for m in metrics:
            svc = m.service_name
            if svc not in by_service:
                by_service[svc] = {}
            if m.metric_name not in by_service[svc]:
                by_service[svc][m.metric_name] = {
                    "value": m.value,
                    "unit": m.unit,
                    "recorded_at": m.recorded_at.isoformat() if m.recorded_at else None,
                }

        return {"type": "metrics", "services": by_service}

    def _get_system_summary(self) -> dict:
        """Get overall system summary."""
        total_incidents = self._db.query(func.count(Incident.id)).scalar() or 0
        open_incidents = self._db.query(func.count(Incident.id)).filter(
            Incident.status != "resolved"
        ).scalar() or 0
        critical = self._db.query(func.count(Incident.id)).filter(
            Incident.severity == "critical",
            Incident.status != "resolved",
        ).scalar() or 0

        recent_alerts = self._db.query(Alert).order_by(
            desc(Alert.created_at)
        ).limit(5).all()

        return {
            "type": "summary",
            "total_incidents": total_incidents,
            "open_incidents": open_incidents,
            "critical_open": critical,
            "health_score": max(0, 100 - open_incidents * 10 - critical * 20),
            "recent_alerts": [
                {"title": a.title, "severity": a.severity}
                for a in recent_alerts
            ],
        }

    # ── Response Generation ────────────────────────────────────────────

    def generate_response(
        self, question: str, data: dict, intent: dict
    ) -> str:
        """
        Generate a natural language response using Claude.

        Falls back to template response if LLM unavailable.
        """
        if not self._client:
            return self._template_response(data, intent)

        try:
            system_prompt = (
                "You are SentryAI, a DevOps assistant. Answer the user's question based on "
                "the provided system data. Be conversational, concise, and helpful. "
                "If data shows issues, highlight them clearly. Use bullet points for lists. "
                "If you don't have enough data, say so honestly."
            )

            # Build context from conversation history
            messages = []
            for msg in self._conversation_history[-6:]:
                messages.append(msg)

            messages.append({
                "role": "user",
                "content": (
                    f"Question: {question}\n\n"
                    f"System data:\n```json\n{self._safe_json(data)}\n```\n\n"
                    "Answer the question based on this data."
                ),
            })

            response = self._client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=500,
                system=system_prompt,
                messages=messages,
            )

            return response.content[0].text

        except Exception as e:
            logger.error(f"LLM response generation failed: {e}")
            return self._template_response(data, intent)

    def _template_response(self, data: dict, intent: dict) -> str:
        """Generate a template-based response when LLM is unavailable."""
        data_type = data.get("type", "unknown")

        if data_type == "summary":
            return (
                f"System Summary:\n"
                f"- Total incidents: {data.get('total_incidents', 0)}\n"
                f"- Open incidents: {data.get('open_incidents', 0)}\n"
                f"- Critical: {data.get('critical_open', 0)}\n"
                f"- Health score: {data.get('health_score', 0)}%"
            )

        elif data_type == "incidents":
            count = data.get("count", 0)
            if count == 0:
                return "No incidents found matching your query."
            lines = [f"Found {count} incident(s):"]
            for inc in data.get("incidents", [])[:5]:
                lines.append(
                    f"- [{inc['severity'].upper()}] {inc['title']} "
                    f"({inc['status']}) — {inc.get('service', 'N/A')}"
                )
            return "\n".join(lines)

        elif data_type == "service_status":
            open_inc = data.get("open_incidents", [])
            metrics = data.get("metrics", [])
            svc = data.get("service_filter", "all services")
            lines = [f"Status for {svc}:"]
            if open_inc:
                lines.append(f"- {len(open_inc)} open incident(s)")
                for inc in open_inc[:3]:
                    lines.append(f"  [{inc['severity']}] {inc['title']}")
            else:
                lines.append("- No open incidents")
            if metrics:
                lines.append("- Recent metrics:")
                for m in metrics[:5]:
                    lines.append(f"  {m['service']}:{m['metric']} = {m['value']}{m.get('unit', '')}")
            return "\n".join(lines)

        elif data_type == "predictions":
            preds = data.get("active_predictions", [])
            if not preds:
                return "No active predictions. All systems look stable."
            lines = [f"{len(preds)} active prediction(s):"]
            for p in preds:
                lines.append(
                    f"- [{p['severity']}] {p['title']} "
                    f"(~{p.get('hours_until', '?')}h, {p.get('confidence', '?')}% confidence)"
                )
            return "\n".join(lines)

        elif data.get("error"):
            return f"Sorry, I encountered an error: {data['error']}"

        return "I found some data but I'm not sure how to present it. Please try a more specific question."

    def _safe_json(self, data: dict) -> str:
        """Safely serialize data to JSON string for LLM context."""
        import json
        try:
            return json.dumps(data, indent=2, default=str)[:3000]
        except Exception:
            return str(data)[:3000]
