"""Enhanced WebSocket connection manager with per-user tracking, heartbeat, and event buffering."""
from fastapi import WebSocket
from collections import defaultdict
from datetime import datetime
import asyncio
import json
import logging

logger = logging.getLogger(__name__)

# Message types
MSG_NEW_INCIDENT = "new_incident"
MSG_INCIDENT_UPDATED = "incident_updated"
MSG_INCIDENT_RESOLVED = "incident_resolved"
MSG_METRIC_ALERT = "metric_alert"
MSG_METRIC_UPDATE = "metric_update"
MSG_REMEDIATION_STARTED = "remediation_started"
MSG_REMEDIATION_COMPLETED = "remediation_completed"
MSG_PREDICTION_ALERT = "prediction_alert"
MSG_AGENT_STATUS = "agent_status_change"
MSG_DIAGNOSTIC_PROGRESS = "diagnostic_progress"
MSG_COMMENT_ADDED = "comment_added"
MSG_PRESENCE_UPDATE = "presence_update"

HEARTBEAT_INTERVAL = 30  # seconds
EVENT_BUFFER_SIZE = 100


class ConnectionManager:
    """Manages WebSocket connections with per-user tracking, heartbeat, and event buffer."""

    def __init__(self):
        # user_id → list of WebSocket connections
        self.user_connections: dict[str, list[WebSocket]] = defaultdict(list)
        # anonymous connections (legacy support)
        self.active_connections: list[WebSocket] = []
        # service subscriptions: service_name → set of user_ids
        self.service_subscriptions: dict[str, set[str]] = defaultdict(set)
        # Event buffer for reconnection (ring buffer of last N events)
        self._event_buffer: list[dict] = []
        # Connection metadata
        self._connection_meta: dict[WebSocket, dict] = {}
        # Heartbeat task
        self._heartbeat_task: asyncio.Task | None = None

    # ── Connection lifecycle ────────────────────────────────

    async def connect(self, websocket: WebSocket, user_id: str | None = None):
        """Accept connection and register user."""
        await websocket.accept()

        if user_id:
            self.user_connections[user_id].append(websocket)
            self._connection_meta[websocket] = {
                "user_id": user_id,
                "connected_at": datetime.utcnow().isoformat(),
                "last_pong": datetime.utcnow(),
            }
            logger.info(f"WebSocket connected: user={user_id} (total: {self.connection_count})")
        else:
            self.active_connections.append(websocket)

        # Send initial state
        await self._send_json(websocket, {
            "type": "connected",
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
        })

        # Start heartbeat if not running
        if self._heartbeat_task is None or self._heartbeat_task.done():
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    def disconnect(self, websocket: WebSocket, user_id: str | None = None):
        """Remove connection and clean up."""
        if user_id and user_id in self.user_connections:
            conns = self.user_connections[user_id]
            if websocket in conns:
                conns.remove(websocket)
            if not conns:
                del self.user_connections[user_id]
                # Remove from service subscriptions
                for subs in self.service_subscriptions.values():
                    subs.discard(user_id)
        elif websocket in self.active_connections:
            self.active_connections.remove(websocket)

        self._connection_meta.pop(websocket, None)
        logger.info(f"WebSocket disconnected: user={user_id} (total: {self.connection_count})")

    # ── Messaging ───────────────────────────────────────────

    async def broadcast_to_user(self, user_id: str, message: dict):
        """Send message to all connections of a specific user."""
        conns = self.user_connections.get(user_id, [])
        dead = []
        for ws in conns:
            if not await self._send_json(ws, message):
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws, user_id)

    async def broadcast_to_all(self, message: dict):
        """Send to every connected client. Buffers the event for reconnection."""
        self._buffer_event(message)

        # Send to user-tracked connections
        for user_id in list(self.user_connections.keys()):
            await self.broadcast_to_user(user_id, message)

        # Send to anonymous connections
        dead = []
        for ws in self.active_connections:
            if not await self._send_json(ws, message):
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

    async def broadcast_by_service(self, service_name: str, message: dict):
        """Send to users subscribed to a specific service."""
        subscribers = self.service_subscriptions.get(service_name, set())
        for user_id in subscribers:
            await self.broadcast_to_user(user_id, message)
        # Also broadcast to anonymous connections (legacy)
        await self.broadcast(message)

    async def broadcast(self, message: dict):
        """Legacy broadcast to anonymous connections."""
        dead = []
        for ws in self.active_connections:
            if not await self._send_json(ws, message):
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

    # ── Typed broadcasts ────────────────────────────────────

    async def broadcast_alert(self, alert: dict):
        await self.broadcast_to_all({"type": MSG_METRIC_ALERT, "data": alert})

    async def broadcast_metrics(self, metrics: dict):
        await self.broadcast_to_all({"type": MSG_METRIC_UPDATE, "data": metrics})

    async def broadcast_incident(self, event_type: str, incident: dict):
        await self.broadcast_to_all({"type": event_type, "data": incident})

    async def broadcast_remediation(self, event_type: str, data: dict):
        await self.broadcast_to_all({"type": event_type, "data": data})

    async def broadcast_agent_status(self, agent_name: str, status: str):
        await self.broadcast_to_all({
            "type": MSG_AGENT_STATUS,
            "data": {"agent": agent_name, "status": status},
        })

    # ── Subscriptions ───────────────────────────────────────

    def subscribe_to_service(self, user_id: str, service_name: str):
        self.service_subscriptions[service_name].add(user_id)

    def unsubscribe_from_service(self, user_id: str, service_name: str):
        self.service_subscriptions.get(service_name, set()).discard(user_id)

    # ── Heartbeat ───────────────────────────────────────────

    async def _heartbeat_loop(self):
        """Ping all clients every HEARTBEAT_INTERVAL seconds; drop stale ones."""
        while self.connection_count > 0:
            await asyncio.sleep(HEARTBEAT_INTERVAL)
            stale: list[tuple[WebSocket, str | None]] = []

            for user_id, conns in list(self.user_connections.items()):
                for ws in conns:
                    ok = await self._send_json(ws, {"type": "ping"})
                    if not ok:
                        stale.append((ws, user_id))

            for ws in list(self.active_connections):
                ok = await self._send_json(ws, {"type": "ping"})
                if not ok:
                    stale.append((ws, None))

            for ws, uid in stale:
                self.disconnect(ws, uid)

    def handle_pong(self, websocket: WebSocket):
        """Record pong response from client."""
        meta = self._connection_meta.get(websocket)
        if meta:
            meta["last_pong"] = datetime.utcnow()

    # ── Event buffer for reconnection ───────────────────────

    def _buffer_event(self, event: dict):
        event["_buffered_at"] = datetime.utcnow().isoformat()
        self._event_buffer.append(event)
        if len(self._event_buffer) > EVENT_BUFFER_SIZE:
            self._event_buffer = self._event_buffer[-EVENT_BUFFER_SIZE:]

    async def send_missed_events(self, websocket: WebSocket, since: str | None = None):
        """Send buffered events that occurred after `since` timestamp."""
        events = self._event_buffer
        if since:
            events = [e for e in events if e.get("_buffered_at", "") > since]
        for event in events:
            await self._send_json(websocket, event)

    # ── Helpers ─────────────────────────────────────────────

    async def _send_json(self, websocket: WebSocket, data: dict) -> bool:
        try:
            await websocket.send_text(json.dumps(data, default=str))
            return True
        except Exception:
            return False

    @property
    def connection_count(self) -> int:
        user_count = sum(len(c) for c in self.user_connections.values())
        return user_count + len(self.active_connections)

    def get_online_users(self) -> list[str]:
        return list(self.user_connections.keys())

    def get_stats(self) -> dict:
        return {
            "total_connections": self.connection_count,
            "authenticated_users": len(self.user_connections),
            "anonymous_connections": len(self.active_connections),
            "buffered_events": len(self._event_buffer),
            "service_subscriptions": {k: len(v) for k, v in self.service_subscriptions.items()},
        }


# Singleton
manager = ConnectionManager()
