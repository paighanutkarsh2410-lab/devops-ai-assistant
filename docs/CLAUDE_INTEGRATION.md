# Claude API Integration

The DevOps Assistant uses the Anthropic Claude API for AI-powered incident analysis.

## Overview

Claude analyzes incidents by receiving structured context (metrics, logs, deployments, past incidents) and returning a JSON diagnosis with root cause, confidence score, and recommended actions.

## Model Configuration

- **Model**: `claude-sonnet-4-20250514`
- **Max tokens**: 1024 (analysis), 2048 (reports)
- **Temperature**: 0 (deterministic output)
- **Retry logic**: 3 attempts with exponential backoff for rate limit errors

## API Functions

### `analyze_incident(incident, metrics, logs, deployments, similar_incidents)`

Primary analysis function. Builds a detailed prompt with all context and requests structured JSON output.

**Returns:**
```json
{
  "root_cause": "Description of the root cause",
  "confidence": 85,
  "reasoning": "Step-by-step analysis...",
  "recommended_actions": ["action1", "action2"],
  "severity_assessment": "critical"
}
```

### `generate_timeline_summary(events)`

Generates a natural language summary of a timeline of events.

### `generate_incident_report(incident, analysis, timeline)`

Creates a full post-incident report in markdown format.

### `_fallback_analysis()`

Rule-based fallback when the Claude API is unavailable. Provides basic analysis without AI.

## Error Handling

- **Rate limits**: Exponential backoff with 3 retries
- **API errors**: Falls back to rule-based analysis
- **Timeout**: 30-second request timeout
- **Missing API key**: Logs warning and uses fallback

## Prompt Design

The analysis prompt includes:
1. Incident details (title, description, severity, service)
2. Recent metrics with values and units
3. Error log entries with timestamps
4. Recent deployments with versions
5. Similar past incidents (if any)

The system prompt instructs Claude to act as a senior SRE and return strictly formatted JSON.

## Security

- API key stored in `.env` file (never committed)
- Key loaded via `python-dotenv`
- No sensitive data included in prompts beyond service names and metrics
