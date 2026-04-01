from fastapi import WebSocket
from typing import List
import json


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """Send message to all connected clients."""
        dead = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception:
                dead.append(connection)
        for conn in dead:
            self.disconnect(conn)

    async def broadcast_alert(self, alert: dict):
        await self.broadcast({"type": "alert", "data": alert})

    async def broadcast_metrics(self, metrics: dict):
        await self.broadcast({"type": "metrics", "data": metrics})


# Singleton
manager = ConnectionManager()
