from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
    Depends,
    Query,
    HTTPException,
    status,
)
from fastapi.security import HTTPBearer  # , HTTPAuthorizationCredentials
import json
from typing import Optional
from datetime import datetime
from backend.utils.logger import logger


router = APIRouter(prefix="/ws", tags=["websocket"])
security = HTTPBearer(auto_error=False)


@router.websocket("/monitoring")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: Optional[str] = Query(None, description="Client identifier"),
    token: Optional[str] = Query(None, description="Authentication token"),
):
    """
    WebSocket endpoint for real-time experiment monitoring.
    Accepts token as query parameter or will try to get from headers after upgrade.
    """
    # Accept the connection first
    await websocket.accept()

    try:
        # Simple authentication - you can customize this
        if not client_id or not client_id.startswith("experiment_"):
            await websocket.send_json(
                {
                    "type": "error",
                    "message": "Invalid client_id format. Must be experiment_<id>",
                }
            )
            await websocket.close(code=1008, reason="Invalid client_id")
            return

        # Extract experiment_id from client_id
        experiment_id = client_id.replace("experiment_", "")

        # Send connection confirmation
        await websocket.send_json(
            {
                "type": "connected",
                "client_id": client_id,
                "experiment_id": experiment_id,
                "timestamp": datetime.now().isoformat(),
            }
        )

        logger.info(f"WebSocket connected for experiment {experiment_id}")

        # Handle messages
        while True:
            try:
                message = await websocket.receive_text()
                data = json.loads(message)

                if data.get("type") == "ping":
                    await websocket.send_json(
                        {"type": "pong", "timestamp": datetime.now().isoformat()}
                    )
                elif data.get("type") == "subscribe":
                    topics = data.get("topics", [])
                    await websocket.send_json(
                        {
                            "type": "subscribed",
                            "topics": topics,
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for experiment {experiment_id}")
                break
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await websocket.send_json({"type": "error", "message": str(e)})

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.close(code=1011, reason=str(e))
        except:
            pass
