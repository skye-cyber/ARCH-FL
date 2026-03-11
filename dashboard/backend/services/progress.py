from typing import Dict, Any, Optional, Callable, List
from datetime import datetime, timedelta
import threading
from ..core.progress_tracker import ProgressManager, ProgressTracker
from ..models.responses import ExperimentResponse
from ..utils.logger import logger


class ProgressService:
    """
    Service for managing progress tracking across the application
    """

    def __init__(self):
        self.progress_manager = ProgressManager()
        self._listeners: Dict[str, List[Callable]] = {}
        self._lock = threading.Lock()

    def create_tracker(
        self, task_id: str, total_steps: int = 100, description: str = ""
    ) -> ProgressTracker:
        """Create a new progress tracker"""
        tracker = self.progress_manager.create_tracker(task_id, total_steps)
        tracker.message = description

        # Register internal callback for logging
        def log_progress(tid: str, progress: int, message: str):
            if progress % 10 == 0 or progress == 100:  # Log every 10%
                logger.debug(f"Task {tid}: {progress}% - {message}")

        tracker.register_callback(log_progress)

        return tracker

    def update_progress(
        self, task_id: str, progress: int, message: Optional[str] = None
    ):
        """Update progress for a task"""
        tracker = self.progress_manager.get_tracker(task_id)
        if tracker:
            tracker.update(progress, message)
            self._notify_listeners(task_id, tracker.get_status())

    def increment_progress(
        self, task_id: str, steps: int = 1, message: Optional[str] = None
    ):
        """Increment progress for a task"""
        tracker = self.progress_manager.get_tracker(task_id)
        if tracker:
            tracker.increment(steps, message)
            self._notify_listeners(task_id, tracker.get_status())

    def complete_progress(self, task_id: str, message: Optional[str] = None):
        """Mark task as complete"""
        tracker = self.progress_manager.get_tracker(task_id)
        if tracker:
            tracker.complete(message)
            self._notify_listeners(task_id, tracker.get_status())

    def fail_progress(self, task_id: str, error: str):
        """Mark task as failed"""
        tracker = self.progress_manager.get_tracker(task_id)
        if tracker:
            tracker.fail(error)
            self._notify_listeners(task_id, tracker.get_status())

    def get_progress(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get progress status for a task"""
        tracker = self.progress_manager.get_tracker(task_id)
        if tracker:
            return tracker.get_status()
        return None

    def get_progress_response(self, task_id: str) -> Optional[ExperimentResponse]:
        """Get progress as API response model"""
        status = self.get_progress(task_id)
        if not status:
            return None

        return ExperimentResponse(
            task_id=task_id,
            status=status.get("status", "unknown"),
            progress=status.get("progress", 0),
            message=status.get("message", ""),
            logs=[],  # Logs are handled elsewhere
            created_at=status.get("start_time"),
            started_at=status.get("start_time"),
            completed_at=status.get("end_time"),
        )

    def register_listener(self, task_id: str, callback: Callable):
        """Register a listener for task progress updates"""
        with self._lock:
            if task_id not in self._listeners:
                self._listeners[task_id] = []
            self._listeners[task_id].append(callback)

    def unregister_listener(self, task_id: str, callback: Callable):
        """Unregister a listener"""
        with self._lock:
            if task_id in self._listeners and callback in self._listeners[task_id]:
                self._listeners[task_id].remove(callback)

    def _notify_listeners(self, task_id: str, status: Dict[str, Any]):
        """Notify all listeners of progress update"""
        with self._lock:
            listeners = self._listeners.get(task_id, []).copy()

        for callback in listeners:
            try:
                callback(task_id, status)
            except Exception as e:
                logger.error(f"Error in progress listener for task {task_id}: {e}")

    def cleanup_old_trackers(self, max_age_minutes: int = 60):
        """Remove old trackers"""
        self.progress_manager.cleanup_old_trackers(max_age_minutes)

        # Also clean up listeners for removed trackers
        cutoff = datetime.now() - timedelta(minutes=max_age_minutes)

        with self._lock:
            to_remove = []
            for task_id in self._listeners:
                tracker = self.progress_manager.get_tracker(task_id)
                if not tracker or (tracker.start_time and tracker.start_time < cutoff):
                    to_remove.append(task_id)

            for task_id in to_remove:
                del self._listeners[task_id]

    def get_active_tasks(self) -> List[Dict[str, Any]]:
        """Get all active tasks with their progress"""
        active = []

        for task_id, tracker in self.progress_manager.trackers.items():
            if not tracker.is_completed and not tracker.is_failed:
                active.append(tracker.get_status())

        return active

    def get_statistics(self) -> Dict[str, Any]:
        """Get progress statistics"""
        total = len(self.progress_manager.trackers)
        completed = sum(
            1 for t in self.progress_manager.trackers.values() if t.is_completed
        )
        failed = sum(1 for t in self.progress_manager.trackers.values() if t.is_failed)
        active = total - completed - failed

        return {
            "total": total,
            "active": active,
            "completed": completed,
            "failed": failed,
            "active_tasks": self.get_active_tasks(),
        }
