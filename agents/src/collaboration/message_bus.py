"""
Message Bus: Reliable message routing between agents with persistence,
delivery guarantees, and dead letter queue.
"""
import uuid
import time
import logging
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


@dataclass
class BusMessage:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    topic: str = ""
    sender: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    delivered: bool = False
    retries: int = 0
    max_retries: int = 3


class MessageBus:
    """
    Central message routing for inter-agent communication.
    Supports pub/sub topics, point-to-point, and dead letter queue.
    """

    def __init__(self, max_queue_size: int = 1000):
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._queues: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_queue_size))
        self._dead_letters: deque = deque(maxlen=200)
        self._message_log: deque = deque(maxlen=5000)
        self._lock = threading.Lock()
        self._stats = {
            "published": 0, "delivered": 0, "failed": 0,
            "dead_letters": 0, "topics": set(),
        }

    # ── Pub/Sub ───────────────────────────────────────────────────────

    def subscribe(self, topic: str, handler: Callable[[BusMessage], None]):
        """Subscribe to a topic."""
        with self._lock:
            self._subscribers[topic].append(handler)
            self._stats["topics"].add(topic)

    def unsubscribe(self, topic: str, handler: Callable):
        with self._lock:
            subs = self._subscribers.get(topic, [])
            self._subscribers[topic] = [h for h in subs if h != handler]

    def publish(self, topic: str, sender: str, payload: Dict[str, Any]) -> str:
        """Publish a message to a topic. Returns message ID."""
        msg = BusMessage(topic=topic, sender=sender, payload=payload)
        self._stats["published"] += 1
        self._message_log.append(msg)

        handlers = self._subscribers.get(topic, [])
        if not handlers:
            self._queues[topic].append(msg)
            return msg.id

        for handler in handlers:
            self._deliver(msg, handler)

        return msg.id

    def _deliver(self, msg: BusMessage, handler: Callable):
        """Deliver a message with retry logic."""
        try:
            handler(msg)
            msg.delivered = True
            self._stats["delivered"] += 1
        except Exception as e:
            msg.retries += 1
            if msg.retries >= msg.max_retries:
                self._dead_letters.append({"message": msg, "error": str(e),
                                           "timestamp": datetime.now(timezone.utc).isoformat()})
                self._stats["dead_letters"] += 1
                self._stats["failed"] += 1
                logger.warning(f"[MessageBus] Dead letter: {msg.id} on {msg.topic}: {e}")
            else:
                self._deliver(msg, handler)

    # ── Point-to-Point ────────────────────────────────────────────────

    def send(self, recipient: str, sender: str, payload: Dict[str, Any]) -> str:
        """Send a direct message to a specific agent's queue."""
        msg = BusMessage(topic=f"direct:{recipient}", sender=sender, payload=payload)
        self._queues[f"direct:{recipient}"].append(msg)
        self._stats["published"] += 1
        self._message_log.append(msg)
        return msg.id

    def receive(self, agent_name: str, max_messages: int = 10) -> List[BusMessage]:
        """Receive messages from an agent's queue."""
        queue_key = f"direct:{agent_name}"
        messages = []
        with self._lock:
            queue = self._queues.get(queue_key, deque())
            while queue and len(messages) < max_messages:
                msg = queue.popleft()
                msg.delivered = True
                messages.append(msg)
                self._stats["delivered"] += 1
        return messages

    # ── Drain pending messages for a topic ────────────────────────────

    def drain_topic(self, topic: str) -> List[BusMessage]:
        """Get all queued messages for a topic."""
        with self._lock:
            queue = self._queues.get(topic, deque())
            messages = list(queue)
            queue.clear()
        return messages

    # ── Dead Letter Queue ─────────────────────────────────────────────

    def get_dead_letters(self, limit: int = 50) -> List[Dict[str, Any]]:
        return list(self._dead_letters)[-limit:]

    def retry_dead_letters(self, topic: Optional[str] = None) -> int:
        """Retry failed messages. Returns count retried."""
        retried = 0
        remaining = []
        for entry in self._dead_letters:
            msg = entry["message"]
            if topic and msg.topic != topic:
                remaining.append(entry)
                continue
            msg.retries = 0
            handlers = self._subscribers.get(msg.topic, [])
            for h in handlers:
                self._deliver(msg, h)
            retried += 1
        self._dead_letters.clear()
        self._dead_letters.extend(remaining)
        return retried

    # ── Monitoring ────────────────────────────────────────────────────

    def get_message_flow(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent message flow for visualization."""
        return [
            {
                "id": m.id, "topic": m.topic, "sender": m.sender,
                "delivered": m.delivered, "timestamp": m.timestamp,
            }
            for m in list(self._message_log)[-limit:]
        ]

    def get_topic_stats(self) -> Dict[str, Any]:
        """Per-topic statistics."""
        topic_counts: Dict[str, int] = defaultdict(int)
        for m in self._message_log:
            topic_counts[m.topic] += 1
        return dict(topic_counts)

    @property
    def stats(self) -> Dict[str, Any]:
        return {
            "published": self._stats["published"],
            "delivered": self._stats["delivered"],
            "failed": self._stats["failed"],
            "dead_letters": self._stats["dead_letters"],
            "active_topics": len(self._stats["topics"]),
            "queue_depths": {k: len(v) for k, v in self._queues.items() if v},
        }
