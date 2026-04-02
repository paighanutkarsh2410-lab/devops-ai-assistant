"""
Claude API integration for intelligent incident analysis.
Provides root cause analysis, incident reports, and diagnostic reasoning.
"""
import anthropic
import json
import time
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

_client = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return _client


def call_claude(prompt: str, system: str = "", max_tokens: int = 2048,
                retries: int = MAX_RETRIES) -> Optional[str]:
    """Call Claude API with retry logic."""
    client = _get_client()

    for attempt in range(retries):
        try:
            messages = [{"role": "user", "content": prompt}]
            kwargs = {
                "model": "claude-sonnet-4-20250514",
                "max_tokens": max_tokens,
                "messages": messages,
            }
            if system:
                kwargs["system"] = system

            response = client.messages.create(**kwargs)
            return response.content[0].text

        except anthropic.RateLimitError:
            if attempt < retries - 1:
                wait = RETRY_DELAY * (2 ** attempt)
                print(f"  [LLM] Rate limited, waiting {wait}s...")
                time.sleep(wait)
            else:
                print("  [LLM] Rate limit exceeded after retries")
                return None
        except anthropic.APIError as e:
            print(f"  [LLM] API error: {e}")
            if attempt < retries - 1:
                time.sleep(RETRY_DELAY)
            else:
                return None
        except Exception as e:
            print(f"  [LLM] Unexpected error: {e}")
            return None

    return None


def analyze_incident(incident: dict, metrics: list, logs: list,
                     deployments: list, similar_incidents: list = None) -> dict:
    """
    Analyze an incident using Claude to determine root cause.
    Returns structured analysis with root cause, confidence, and recommendations.
    """
    system = """You are an expert DevOps engineer and Site Reliability Engineer (SRE).
You analyze infrastructure incidents to determine root causes and recommend fixes.
Always respond in valid JSON format with these exact fields:
{
  "root_cause": "string describing the most likely root cause",
  "confidence": integer 0-100,
  "reasoning": "string explaining your analysis",
  "recommended_actions": ["action1", "action2", ...],
  "severity_assessment": "critical|high|medium|low",
  "similar_pattern": "description of any known pattern this matches"
}"""

    # Build context
    metrics_summary = _format_metrics(metrics)
    logs_summary = _format_logs(logs)
    deploy_summary = _format_deployments(deployments)
    similar_summary = _format_similar(similar_incidents) if similar_incidents else "None found."

    prompt = f"""Analyze this infrastructure incident and determine the root cause.

## Incident
- Title: {incident.get('title', 'Unknown')}
- Description: {incident.get('description', 'No description')}
- Severity: {incident.get('severity', 'unknown')}
- Service: {incident.get('service_name', 'unknown')}
- Detected at: {incident.get('detected_at', 'unknown')}

## Recent Metrics (last 1 hour)
{metrics_summary}

## Recent Logs
{logs_summary}

## Recent Deployments (last 24 hours)
{deploy_summary}

## Similar Past Incidents
{similar_summary}

Analyze all the data and determine the most likely root cause. Consider correlations between
deployments, metric changes, and error patterns. Respond ONLY with the JSON object."""

    response = call_claude(prompt, system=system, max_tokens=1500)

    if not response:
        return _fallback_analysis(incident, metrics)

    try:
        # Extract JSON from response (handle markdown code blocks)
        text = response.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to extract JSON from within the response
        try:
            start = response.index("{")
            end = response.rindex("}") + 1
            return json.loads(response[start:end])
        except (ValueError, json.JSONDecodeError):
            return _fallback_analysis(incident, metrics)


def generate_timeline_summary(events: list) -> str:
    """Generate a natural language summary of incident timeline events."""
    if not events:
        return "No timeline events available."

    events_text = "\n".join([
        f"- [{e.get('timestamp', '?')}] {e.get('event_type', '?')}: {e.get('description', '?')}"
        for e in events
    ])

    prompt = f"""Write a clear, concise narrative summary of this incident timeline.
Write it as a short paragraph suitable for a post-incident review.

Timeline events:
{events_text}

Write the summary in 2-3 sentences. Be specific about times and causes."""

    response = call_claude(prompt, max_tokens=500)
    return response or "Timeline summary unavailable."


def generate_incident_report(incident: dict, analysis: dict, timeline: list) -> str:
    """Generate a full incident report in natural language."""
    prompt = f"""Write a professional post-incident report for this infrastructure event.

Incident: {incident.get('title', 'Unknown')}
Service: {incident.get('service_name', 'Unknown')}
Severity: {incident.get('severity', 'Unknown')}
Root Cause: {analysis.get('root_cause', 'Under investigation')}
Confidence: {analysis.get('confidence', 0)}%

Timeline: {json.dumps(timeline[:10], default=str)}
Recommended Actions: {json.dumps(analysis.get('recommended_actions', []))}

Format the report with sections: Summary, Impact, Root Cause, Timeline, Action Items.
Keep it under 300 words."""

    response = call_claude(prompt, max_tokens=1000)
    return response or "Report generation failed."


def _format_metrics(metrics: list) -> str:
    if not metrics:
        return "No metric data available."
    lines = []
    for m in metrics[:20]:
        lines.append(f"  {m.get('service_name', '?')}/{m.get('metric_name', '?')}: "
                     f"{m.get('value', 0):.1f}{m.get('unit', '')} at {m.get('timestamp', '?')}")
    return "\n".join(lines)


def _format_logs(logs: list) -> str:
    if not logs:
        return "No log data available."
    lines = []
    for log in logs[:15]:
        lines.append(f"  [{log.get('level', '?')}] {log.get('timestamp', '?')}: {log.get('message', '?')}")
    return "\n".join(lines)


def _format_deployments(deployments: list) -> str:
    if not deployments:
        return "No recent deployments."
    lines = []
    for d in deployments[:5]:
        lines.append(f"  {d.get('service_name', '?')} v{d.get('version', '?')} "
                     f"at {d.get('deployed_at', '?')} by {d.get('deployed_by', '?')}")
    return "\n".join(lines)


def _format_similar(incidents: list) -> str:
    if not incidents:
        return "None found."
    lines = []
    for inc in incidents[:3]:
        lines.append(f"  - {inc.get('title', '?')} (similarity: {inc.get('score', 0):.0%})")
        if inc.get('root_cause'):
            lines.append(f"    Root cause: {inc['root_cause']}")
    return "\n".join(lines)


def _fallback_analysis(incident: dict, metrics: list) -> dict:
    """Rule-based fallback when Claude API is unavailable."""
    root_cause = "Unable to determine - AI analysis unavailable"
    severity = incident.get("severity", "medium")
    confidence = 30

    # Simple rule-based analysis
    for m in metrics:
        if m.get("metric_name") == "cpu" and m.get("value", 0) > 90:
            root_cause = f"High CPU usage ({m['value']:.0f}%) on {m.get('service_name', 'unknown')}"
            confidence = 60
            break
        elif m.get("metric_name") == "memory" and m.get("value", 0) > 90:
            root_cause = f"Memory exhaustion ({m['value']:.0f}%) on {m.get('service_name', 'unknown')}"
            confidence = 60
            break
        elif m.get("metric_name") == "error_rate" and m.get("value", 0) > 5:
            root_cause = f"High error rate ({m['value']:.1f}/min) on {m.get('service_name', 'unknown')}"
            confidence = 55
            break

    return {
        "root_cause": root_cause,
        "confidence": confidence,
        "reasoning": "Fallback rule-based analysis (Claude API unavailable)",
        "recommended_actions": ["Investigate service logs", "Check recent deployments", "Monitor metrics"],
        "severity_assessment": severity,
        "similar_pattern": "N/A"
    }
