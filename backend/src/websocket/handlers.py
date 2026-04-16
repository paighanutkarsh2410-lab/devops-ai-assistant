"""WebSocket endpoint handlers with per-user authentication and reconnection support."""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from .connection_manager import manager
import json
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws")
async def websocket_anonymous(websocket: WebSocket):
    """Legacy anonymous WebSocket endpoint."""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                elif msg.get("type") == "pong":
                    manager.handle_pong(websocket)
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.websocket("/ws/{user_id}")
async def websocket_user(websocket: WebSocket, user_id: str, last_event: str = Query(None)):
    """Per-user WebSocket with reconnection support."""
    await manager.connect(websocket, user_id)

    # Send missed events on reconnect
    if last_event:
        await manager.send_missed_events(websocket, since=last_event)

    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                msg_type = msg.get("type", "")

                if msg_type == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                elif msg_type == "pong":
                    manager.handle_pong(websocket)
                elif msg_type == "subscribe_service":
                    service = msg.get("service_name")
                    if service:
                        manager.subscribe_to_service(user_id, service)
                elif msg_type == "unsubscribe_service":
                    service = msg.get("service_name")
                    if service:
                        manager.unsubscribe_from_service(user_id, service)
                elif msg_type == "get_stats":
                    await websocket.send_text(json.dumps({
                        "type": "stats",
                        "data": manager.get_stats(),
                    }))
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
