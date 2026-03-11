from typing import Optional
from ..core.experiment_manager import TaskManager
from ..services.progress_service import ProgressService
from ..services.websocket_manager import WebSocketManager
from ..config.settings import settings
from ..utils.logger import logger
from ..services.notification import NotificationService

# Singleton instances
_task_manager: Optional[TaskManager] = None
_websocket_manager: Optional[WebSocketManager] = None
_progress_service: Optional[ProgressService] = None
_notification_service: Optional[NotificationService] = None


def get_task_manager() -> TaskManager:
    """Get or create TaskManager singleton"""
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager(
            storage_path=settings.TASK_STORAGE_PATH,
            filewarp_path=settings.FILEWARP_PATH,
        )
        logger.info("TaskManager initialized")
    return _task_manager


def get_progress_service() -> ProgressService:
    """Get or create ProgressService singleton"""
    global _progress_service
    if _progress_service is None:
        _progress_service = ProgressService()
        logger.info("ProgressService initialized")
    return _progress_service


def get_websocket_manager() -> WebSocketManager:
    """Get or create WebSocketManager singleton"""
    global _websocket_manager
    if _websocket_manager is None:
        _websocket_manager = WebSocketManager()
        logger.info("WebSocketManager initialized")
    return _websocket_manager


def get_notification_service() -> NotificationService:
    """Get or create NotificationService singleton"""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
        logger.info("NotificationService initialized")
    return _notification_service
