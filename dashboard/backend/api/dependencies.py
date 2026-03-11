from typing import Optional
from ..core.experiment_manager import ExperimentManager
from ..services.progress import ProgressService
from ..services.websocket_manager import WebSocketManager
from ..config.settings import settings
from ..utils.logger import logger
from ..services.notification import NotificationService

# Singleton instances
_experiment_manager: Optional[ExperimentManager] = None
_websocket_manager: Optional[WebSocketManager] = None
_progress_service: Optional[ProgressService] = None
_notification_service: Optional[NotificationService] = None


def get_experiment_manager() -> ExperimentManager:
    """Get or create ExperimentManager singleton"""
    global _experiment_manager
    if _experiment_manager is None:
        from backend.core.db import dbmanager
        _experiment_manager = ExperimentManager(
            storage_path=settings.TASK_STORAGE_PATH,
            db_manager=dbmanager,
        )
        logger.info("ExperimentManager initialized")
    return _experiment_manager


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
