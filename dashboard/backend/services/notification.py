from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
import asyncio
from enum import Enum
from warpapp.utils.logger import logger


class NotificationService:
    """
    Service for managing notifications across the application
    """

    def __init__(self):
        self.notifications: Dict[str, Notification] = {}
        self.subscribers: Dict[str, List[Callable]] = {}
        self.user_notifications: Dict[
            str, List[str]
        ] = {}  # user_id -> list of notification_ids
        self._lock = asyncio.Lock()

    async def create_notification(
        self,
        notification_type: NotificationType,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        task_id: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create a new notification
        """
        notification = Notification(
            notification_type=notification_type,
            title=title,
            message=message,
            priority=priority,
            task_id=task_id,
            metadata=metadata,
        )

        async with self._lock:
            self.notifications[notification.id] = notification

            if user_id:
                if user_id not in self.user_notifications:
                    self.user_notifications[user_id] = []
                self.user_notifications[user_id].append(notification.id)

        # Notify subscribers
        await self._notify_subscribers(notification)

        logger.info(f"Created notification {notification.id}: {title}")

        return notification.id

    async def notify_task_started(
        self, task_id: str, operation: str, user_id: Optional[str] = None
    ):
        """Create task started notification"""
        await self.create_notification(
            notification_type=NotificationType.TASK_STARTED,
            title=f"Task Started: {operation}",
            message=f"Task {task_id} has started processing",
            task_id=task_id,
            user_id=user_id,
            metadata={"operation": operation},
        )

    async def notify_task_progress(
        self, task_id: str, progress: int, message: str, user_id: Optional[str] = None
    ):
        """Create task progress notification (for significant milestones)"""
        if progress in [25, 50, 75, 100]:
            await self.create_notification(
                notification_type=NotificationType.TASK_PROGRESS,
                title=f"Task Progress: {progress}%",
                message=message,
                priority=NotificationPriority.LOW,
                task_id=task_id,
                user_id=user_id,
                metadata={"progress": progress},
            )

    async def notify_task_completed(
        self, task_id: str, result: Any, user_id: Optional[str] = None
    ):
        """Create task completed notification"""
        await self.create_notification(
            notification_type=NotificationType.TASK_COMPLETED,
            title="Task Completed",
            message=f"Task {task_id} has completed successfully",
            priority=NotificationPriority.HIGH,
            task_id=task_id,
            user_id=user_id,
            metadata={"result": result},
        )

    async def notify_task_failed(
        self, task_id: str, error: str, user_id: Optional[str] = None
    ):
        """Create task failed notification"""
        await self.create_notification(
            notification_type=NotificationType.TASK_FAILED,
            title="Task Failed",
            message=f"Task {task_id} failed: {error}",
            priority=NotificationPriority.CRITICAL,
            task_id=task_id,
            user_id=user_id,
            metadata={"error": error},
        )

    async def notify_task_cancelled(self, task_id: str, user_id: Optional[str] = None):
        """Create task cancelled notification"""
        await self.create_notification(
            notification_type=NotificationType.TASK_CANCELLED,
            title="Task Cancelled",
            message=f"Task {task_id} was cancelled",
            priority=NotificationPriority.MEDIUM,
            task_id=task_id,
            user_id=user_id,
        )

    async def notify_system_error(self, error: str, user_id: Optional[str] = None):
        """Create system error notification"""
        await self.create_notification(
            notification_type=NotificationType.SYSTEM_ERROR,
            title="System Error",
            message=error,
            priority=NotificationPriority.CRITICAL,
            user_id=user_id,
            metadata={"error": error},
        )

    async def get_user_notifications(
        self, user_id: str, unread_only: bool = False, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get notifications for a user
        """
        result = []

        async with self._lock:
            notification_ids = self.user_notifications.get(user_id, [])[-limit:]

            for nid in notification_ids:
                notification = self.notifications.get(nid)
                if notification and (not unread_only or not notification.read):
                    result.append(
                        {
                            "id": notification.id,
                            "type": notification.type.value,
                            "title": notification.title,
                            "message": notification.message,
                            "priority": notification.priority.value,
                            "task_id": notification.task_id,
                            "created_at": notification.created_at.isoformat(),
                            "read": notification.read,
                            "metadata": notification.metadata,
                        }
                    )

        return sorted(result, key=lambda x: x["created_at"], reverse=True)

    async def mark_as_read(self, notification_id: str, user_id: str) -> bool:
        """
        Mark a notification as read
        """
        async with self._lock:
            if notification_id in self.notifications:
                # Verify ownership
                if (
                    user_id in self.user_notifications
                    and notification_id in self.user_notifications[user_id]
                ):
                    self.notifications[notification_id].read = True
                    return True
        return False

    async def mark_all_as_read(self, user_id: str) -> int:
        """
        Mark all notifications as read for a user
        """
        count = 0

        async with self._lock:
            if user_id in self.user_notifications:
                for nid in self.user_notifications[user_id]:
                    if nid in self.notifications and not self.notifications[nid].read:
                        self.notifications[nid].read = True
                        count += 1

        return count

    async def delete_notification(self, notification_id: str, user_id: str) -> bool:
        """
        Delete a notification
        """
        async with self._lock:
            if (
                user_id in self.user_notifications
                and notification_id in self.user_notifications[user_id]
            ):
                self.user_notifications[user_id].remove(notification_id)

                if notification_id in self.notifications:
                    del self.notifications[notification_id]

                return True
        return False

    async def clear_all_notifications(self, user_id: str) -> int:
        """
        Clear all notifications for a user
        """
        count = 0

        async with self._lock:
            if user_id in self.user_notifications:
                count = len(self.user_notifications[user_id])

                # Remove notifications
                for nid in self.user_notifications[user_id]:
                    if nid in self.notifications:
                        del self.notifications[nid]

                # Clear user's list
                self.user_notifications[user_id] = []

        return count

    def subscribe(
        self,
        callback: Callable,
        notification_types: Optional[List[NotificationType]] = None,
    ):
        """
        Subscribe to notifications
        """
        subscriber_id = f"sub_{datetime.now().timestamp()}"

        self.subscribers[subscriber_id] = {
            "callback": callback,
            "types": notification_types or list(NotificationType),
        }

        return subscriber_id

    def unsubscribe(self, subscriber_id: str):
        """
        Unsubscribe from notifications
        """
        if subscriber_id in self.subscribers:
            del self.subscribers[subscriber_id]

    async def _notify_subscribers(self, notification: Notification):
        """
        Notify all subscribers of a new notification
        """
        for subscriber in self.subscribers.values():
            if notification.type in subscriber["types"]:
                try:
                    await subscriber["callback"](notification)
                except Exception as e:
                    logger.error(f"Error notifying subscriber: {e}")

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get notification statistics
        """
        total = len(self.notifications)
        unread = sum(1 for n in self.notifications.values() if not n.read)

        by_type = {}
        for n in self.notifications.values():
            by_type[n.type.value] = by_type.get(n.type.value, 0) + 1

        return {
            "total": total,
            "unread": unread,
            "by_type": by_type,
            "users_with_notifications": len(self.user_notifications),
        }
