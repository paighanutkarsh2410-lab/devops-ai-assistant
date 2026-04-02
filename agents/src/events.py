"""
Event system for inter-agent communication via Redis pub/sub.
"""
import json
import redis
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Event types
ANOMALY_DETECTED = "anomaly_detected"
INCIDENT_CREATED = "incident_created"
DIAGNOSIS_STARTED = "diagnosis_started"
DIAGNOSIS_COMPLETE = "diagnosis_complete"
REMEDIATION_STARTED = "remediation_started"
REMEDIATION_COMPLETE = "remediation_complete"

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
            "timestamp": datetime.utcnow().isoformat()
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
