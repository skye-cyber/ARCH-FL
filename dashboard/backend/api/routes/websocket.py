from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
import json
from typing import Optional
from backend.services.websocket_manager import WebSocketManager, websocketmanager
from backend.api.dependencies import get_websocket_manager

router = APIRouter(prefix="/ws", tags=["websocket"])


# WebSocket endpoint for real-time monitoring


@router.websocket("/monitoring")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: Optional[str] = Query(None, description="Client identifier"),
    ws_manager: WebSocketManager = Depends(get_websocket_manager),
):
    """WebSocket endpoint for real-time experiment monitoring."""
    await websocketmanager.connect(websocket, "monitoring")
    try:
        while True:
            message = await websocket.receive_text()
            data = json.loads(message)

            if data.get("type") == "ping":
                await websocket.send_json(
                    {"type": "pong", "timestamp": data.get("timestamp")}
                )

            elif data.get("type") == "subscribe":
                # Subscribe to specific event types
                topics = data.get("topics", [])
                await websocket.send_json({"type": "subscribed", "topics": topics})
            await websocketmanager.send_personal_message(
                f"Message received: {data}", websocket
            )
    except WebSocketDisconnect:
        websocketmanager.disconnect(websocket)
