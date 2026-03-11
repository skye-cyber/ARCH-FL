from fastapi import APIRouter
from fastapi import WebSocket, WebSocketDisconnect
from ...services.websocket_manager import websocketmanager

router = APIRouter(prefix="/ws", tags=["websocket"])


# WebSocket endpoint for real-time monitoring


@router.websocket("/ws/monitoring")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time experiment monitoring."""
    await websocketmanager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Here you would handle incoming messages
            # For now, just echo back
            await websocketmanager.send_personal_message(
                f"Message received: {data}", websocket
            )
    except WebSocketDisconnect:
        websocketmanager.disconnect(websocket)
