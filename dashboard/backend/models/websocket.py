from enum import Enum


class WebSocketMessageType(str, Enum):
    """WebSocket message types"""

    PROGRESS_UPDATE = "progress_update"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_CANCELLED = "task_cancelled"
    LOG_MESSAGE = "log_message"
    PING = "ping"
    PONG = "pong"
    ERROR = "error"
    CONNECTED = "connected"
