from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime


class NotificationType(str, Enum):
    """Types of notifications"""

    TASK_STARTED = "task_started"
    TASK_PROGRESS = "task_progress"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_CANCELLED = "task_cancelled"
    SYSTEM_INFO = "system_info"
    SYSTEM_WARNING = "system_warning"
    SYSTEM_ERROR = "system_error"
    USER_MESSAGE = "user_message"


class NotificationPriority(str, Enum):
    """Priority levels for notifications"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Notification:
    """Notification model"""

    def __init__(
        self,
        notification_type: NotificationType,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):

        self.id = f"notif_{datetime.now().timestamp()}"
        self.type = notification_type
        self.title = title
        self.message = message
        self.priority = priority
        self.task_id = task_id
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        self.read = False
        self.delivered = False
