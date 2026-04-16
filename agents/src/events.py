"""
Event system for inter-agent communication via Redis pub/sub.
"""
import json
import redis
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Event types
ANOMALY_DETECTED = "anomaly_detected"
INCIDENT_CREATED = "incident_created"
DIAGNOSIS_STARTED = "diagnosis_started"
DIAGNOSIS_COMPLETE = "diagnosis_complete"
REMEDIATION_STARTED = "remediation_started"
ACTION_EXECUTED = "action_executed"
ACTION_ROLLED_BACK = "action_rolled_back"
APPROVAL_REQUESTED = "approval_requested"
APPROVAL_GRANTED = "approval_granted"
REMEDIATION_COMPLETE = "remediation_complete"
VERIFICATION_COMPLETE = "verification_complete"
LEARNING_STARTED = "learning_started"
LEARNING_COMPLETE = "learning_complete"
PATTERN_DISCOVERED = "pattern_discovered"
RECOMMENDATION_MADE = "recommendation_made"
PREDICTION_STARTED = "prediction_started"
PREDICTION_COMPLETE = "prediction_complete"
CAPACITY_BREACH_PREDICTED = "capacity_breach_predicted"
COST_OVERRUN_PREDICTED = "cost_overrun_predicted"
NOTIFICATION_SENT = "notification_sent"
NOTIFICATION_FAILED = "notification_failed"

CHANNEL = "devops_agent_events"


def _get_redis():
    return redis.from_url(REDIS_URL, decode_responses=True)


def publish_event(event_type: str, data: dict):
    """Publish an event to Redis."""
    try:
        r = _get_redis()
        message = json.dumps({
            "type": event_type,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        r.publish(CHANNEL, message)
    except Exception as e:
        print(f"  [Events] Failed to publish {event_type}: {e}")


def subscribe_events(callback):
    """
    Subscribe to agent events. Calls callback(event_type, data) for each event.
    This is blocking -- run in a thread.
    """
    try:
        r = _get_redis()
        pubsub = r.pubsub()
        pubsub.subscribe(CHANNEL)

        for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    event = json.loads(message["data"])
                    callback(event.get("type"), event.get("data", {}))
                except json.JSONDecodeError:
                    pass
    except Exception as e:
        print(f"  [Events] Subscription error: {e}")
