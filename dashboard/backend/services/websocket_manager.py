from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Optional, Any, Dict, Set
import asyncio
from datetime import datetime
from ..utils.logger import logger
from ..models.websocket import WebSocketMessageType


class WebSocketManager:
    """
    Manages WebSocket connections for real-time updates
    """

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.connection_info: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
        self.ping_interval = 30  # seconds
        self._ping_task = None

    async def connect(
        self, websocket: WebSocket, task_id: str, client_id: Optional[str] = None
    ):
        """
        Accept and register a WebSocket connection
        """
        await websocket.accept()

        client_id = client_id or f"client_{datetime.now().timestamp()}"

        async with self._lock:
            if task_id not in self.active_connections:
                self.active_connections[task_id] = set()

            self.active_connections[task_id].add(websocket)
            self.connection_info[id(websocket)] = {
                "task_id": task_id,
                "client_id": client_id,
                "connected_at": datetime.now(),
                "last_ping": datetime.now(),
                "last_pong": datetime.now(),
            }

        # Send connection confirmation
        await self.send_message(
            websocket,
            {
                "type": WebSocketMessageType.CONNECTED,
                "task_id": task_id,
                "client_id": client_id,
                "timestamp": datetime.now().isoformat(),
            },
        )

        logger.info(f"WebSocket connected for task {task_id} (client: {client_id})")

    async def disconnect(self, websocket: WebSocket, task_id: Optional[str] = None):
        """
        Disconnect and unregister a WebSocket connection
        """
        conn_id = id(websocket)

        async with self._lock:
            # Find which task this connection belongs to
            if task_id is None and conn_id in self.connection_info:
                task_id = self.connection_info[conn_id].get("task_id")

            if task_id and task_id in self.active_connections:
                self.active_connections[task_id].discard(websocket)

                # Clean up empty task sets
                if not self.active_connections[task_id]:
                    del self.active_connections[task_id]

            # Remove connection info
            if conn_id in self.connection_info:
                client_id = self.connection_info[conn_id].get("client_id", "unknown")
                logger.info(
                    f"WebSocket disconnected for task {task_id} (client: {client_id})"
                )
                del self.connection_info[conn_id]

        try:
            await websocket.close()
        except:
            pass

    async def broadcast_to_task(self, task_id: str, message: Dict[str, Any]):
        """
        Broadcast a message to all connections for a specific task
        """
        if task_id not in self.active_connections:
            return

        disconnected = set()

        for connection in self.active_connections[task_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to task {task_id}: {e}")
                disconnected.add(connection)

        # Clean up disconnected connections
        if disconnected:
            async with self._lock:
                for conn in disconnected:
                    self.active_connections[task_id].discard(conn)
                    if id(conn) in self.connection_info:
                        del self.connection_info[id(conn)]

    async def send_message(self, websocket: WebSocket, message: Dict[str, Any]):
        """
        Send a message to a specific WebSocket
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            # Find and remove this connection
            conn_id = id(websocket)
            if conn_id in self.connection_info:
                task_id = self.connection_info[conn_id].get("task_id")
                await self.disconnect(websocket, task_id)

    async def send_progress_update(
        self,
        task_id: str,
        progress: int,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Send progress update to all connections for a task
        """
        await self.broadcast_to_task(
            task_id,
            {
                "type": WebSocketMessageType.PROGRESS_UPDATE,
                "task_id": task_id,
                "progress": progress,
                "message": message,
                "metadata": metadata or {},
                "timestamp": datetime.now().isoformat(),
            },
        )

    async def send_task_completed(self, task_id: str, result: Any):
        """
        Send task completion notification
        """
        await self.broadcast_to_task(
            task_id,
            {
                "type": WebSocketMessageType.TASK_COMPLETED,
                "task_id": task_id,
                "result": result,
                "timestamp": datetime.now().isoformat(),
            },
        )

    async def send_task_failed(self, task_id: str, error: str):
        """
        Send task failure notification
        """
        await self.broadcast_to_task(
            task_id,
            {
                "type": WebSocketMessageType.TASK_FAILED,
                "task_id": task_id,
                "error": error,
                "timestamp": datetime.now().isoformat(),
            },
        )

    async def send_task_cancelled(self, task_id: str):
        """
        Send task cancelled notification
        """
        await self.broadcast_to_task(
            task_id,
            {
                "type": WebSocketMessageType.TASK_CANCELLED,
                "task_id": task_id,
                "timestamp": datetime.now().isoformat(),
            },
        )

    async def send_log_message(self, task_id: str, level: str, message: str):
        """
        Send log message to all connections for a task
        """
        await self.broadcast_to_task(
            task_id,
            {
                "type": WebSocketMessageType.LOG_MESSAGE,
                "task_id": task_id,
                "level": level,
                "message": message,
                "timestamp": datetime.now().isoformat(),
            },
        )

    async def handle_client_messages(self, websocket: WebSocket, task_id: str):
        """
        Handle incoming messages from a client
        """
        try:
            while True:
                message = await websocket.receive_json()

                # Update last pong time for ping messages
                if message.get("type") == WebSocketMessageType.PONG:
                    conn_id = id(websocket)
                    if conn_id in self.connection_info:
                        self.connection_info[conn_id]["last_pong"] = datetime.now()

                # Handle other message types as needed
                elif message.get("type") == WebSocketMessageType.PING:
                    await self.send_message(
                        websocket,
                        {
                            "type": WebSocketMessageType.PONG,
                            "timestamp": datetime.now().isoformat(),
                        },
                    )

                else:
                    logger.debug(f"Received message from task {task_id}: {message}")

        except WebSocketDisconnect:
            await self.disconnect(websocket, task_id)
        except Exception as e:
            logger.error(f"Error handling client messages for task {task_id}: {e}")
            await self.disconnect(websocket, task_id)

    async def start_ping_monitor(self):
        """
        Start periodic ping to check connection health
        """
        while True:
            await asyncio.sleep(self.ping_interval)

            async with self._lock:
                now = datetime.now()
                to_remove = []

                for conn_id, info in self.connection_info.items():
                    # Check if connection is stale (no pong in 3 intervals)
                    if (
                        now - info["last_pong"]
                    ).total_seconds() > self.ping_interval * 3:
                        logger.warning(f"Connection {conn_id} is stale, removing")
                        to_remove.append(conn_id)

                # Remove stale connections
                for conn_id in to_remove:
                    info = self.connection_info.get(conn_id)
                    if info:
                        task_id = info.get("task_id")
                        # Find and remove the actual websocket
                        for ws in list(self.active_connections.get(task_id, set())):
                            if id(ws) == conn_id:
                                await self.disconnect(ws, task_id)
                                break

    def get_connection_count(self, task_id: Optional[str] = None) -> int:
        """
        Get number of active connections
        """
        if task_id:
            return len(self.active_connections.get(task_id, set()))

        total = 0
        for connections in self.active_connections.values():
            total += len(connections)
        return total

    def get_connection_info(self, task_id: str) -> list:
        """
        Get information about connections for a task
        """
        conn_list = []

        for conn_id, info in self.connection_info.items():
            if info.get("task_id") == task_id:
                conn_list.append(
                    {
                        "client_id": info.get("client_id"),
                        "connected_at": info.get("connected_at").isoformat()
                        if info.get("connected_at")
                        else None,
                        "last_ping": info.get("last_ping").isoformat()
                        if info.get("last_ping")
                        else None,
                        "last_pong": info.get("last_pong").isoformat()
                        if info.get("last_pong")
                        else None,
                    }
                )

        return conn_list


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


websocketmanager = WebSocketManager()
