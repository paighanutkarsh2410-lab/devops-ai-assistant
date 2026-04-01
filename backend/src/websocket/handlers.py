from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from .connection_manager import manager
import json

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time metric and alert updates."""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive; handle any client messages
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)
