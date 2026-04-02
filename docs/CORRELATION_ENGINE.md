# Correlation Engine

The Correlation Engine links incidents with potential causes by analyzing deployments, metric anomalies, cascading failures, and temporal patterns.

## Correlation Types

### 1. Deployment Correlation (Score: 90)
Checks for deployments within 1 hour of the incident on the affected service or its known dependencies. This is the highest-weighted signal because recent deployments are the most common cause of incidents.

### 2. Cascading Failure Detection (Score: 85)
Checks if services that the affected service depends on are also experiencing active alerts. Uses a predefined service dependency map.

### 3. Metric Spike Detection (Score: 75)
Looks for abnormal metric values on the affected service:
- CPU > 80%
- Memory > 85%
- Error rate > 5 errors/min
- Response time > 500ms

### 4. Time Correlation (Score: 65)
Identifies when multiple incidents are open simultaneously, suggesting a systemic issue rather than isolated failure.

## Scoring

Each correlation type has a fixed base score. The engine returns the highest score among all detected correlations and determines a confidence label:

| Score Range | Label |
|---|---|
| 90+ | Very likely |
| 70-89 | Probably |
| 50-69 | Possibly |
| < 50 | Uncertain |

## Service Dependency Map

```
api-gateway
├── auth-service
└── web-server-01

web-server-01
├── database-primary
└── cache-redis

auth-service
├── database-primary
└── cache-redis
```

## Usage

```python
from correlation_engine import CorrelationEngine

engine = CorrelationEngine(api_get_fn=agent.api_get)
result = engine.correlate_incident(incident)

print(result["likely_cause"])      # "Very likely: Deployment of web-server-01 v2.1.0"
print(result["max_score"])         # 90
print(result["correlations"])      # List of all detected correlations
```

## Extending

To add new correlation types:
1. Add a `_check_*` method to `CorrelationEngine`
2. Return `{"type": "...", "score": N, "description": "...", "data": {...}}` or `None`
3. Call it from `correlate_incident()`
