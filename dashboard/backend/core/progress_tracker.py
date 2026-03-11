import threading
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from collections import deque
from warpapp.utils.logger import logger


class ProgressTracker:
    """
    Tracks progress of operations with ETA calculation
    """

    def __init__(self, task_id: str, total_steps: int = 100):
        self.task_id = task_id
        self.total_steps = total_steps
        self.current_step = 0
        self.start_time = None
        self.end_time = None
        self.is_completed = False
        self.is_failed = False
        self.message = ""
        self.details = {}

        # For ETA calculation
        self.progress_history = deque(maxlen=10)  # Store last 10 progress points
        self._lock = threading.Lock()
        self.callbacks = []

    def start(self):
        """Start tracking progress"""
        with self._lock:
            self.start_time = datetime.now()
            self._record_progress()
        logger.info(f"Task {self.task_id} started")

    def update(self, progress: int, message: Optional[str] = None, **kwargs):
        """
        Update progress
        """
        with self._lock:
            self.current_step = min(progress, self.total_steps)
            if message:
                self.message = message
            if kwargs:
                self.details.update(kwargs)

            self._record_progress()

        # Trigger callbacks
        for callback in self.callbacks:
            try:
                callback(self.task_id, self.current_step, self.message)
            except Exception as e:
                logger.error(f"Error in progress callback: {e}")

    def increment(self, steps: int = 1, message: Optional[str] = None):
        """
        Increment progress by steps
        """
        with self._lock:
            self.current_step = min(self.current_step + steps, self.total_steps)
            if message:
                self.message = message
            self._record_progress()

    def complete(self, message: Optional[str] = None):
        """
        Mark task as complete
        """
        with self._lock:
            self.current_step = self.total_steps
            self.is_completed = True
            self.end_time = datetime.now()
            if message:
                self.message = message
            self._record_progress()

        logger.info(f"Task {self.task_id} completed in {self.get_elapsed_time():.2f}s")

    def fail(self, error: str):
        """
        Mark task as failed
        """
        with self._lock:
            self.is_failed = True
            self.end_time = datetime.now()
            self.message = f"Failed: {error}"

        logger.error(f"Task {self.task_id} failed: {error}")

    def _record_progress(self):
        """Record progress point for ETA calculation"""
        if self.start_time:
            self.progress_history.append(
                {"timestamp": datetime.now(), "progress": self.current_step}
            )

    def get_progress(self) -> int:
        """Get current progress percentage"""
        if self.total_steps == 0:
            return 0
        return int((self.current_step / self.total_steps) * 100)

    def get_eta(self) -> Optional[float]:
        """
        Calculate estimated time remaining in seconds
        """
        if len(self.progress_history) < 2 or self.is_completed:
            return None

        # Calculate progress rate
        first = self.progress_history[0]
        last = self.progress_history[-1]

        time_diff = (last["timestamp"] - first["timestamp"]).total_seconds()
        progress_diff = last["progress"] - first["progress"]

        if progress_diff <= 0 or time_diff <= 0:
            return None

        rate = progress_diff / time_diff  # steps per second
        remaining_steps = self.total_steps - self.current_step

        if rate <= 0:
            return None

        return remaining_steps / rate

    def get_elapsed_time(self) -> float:
        """Get elapsed time in seconds"""
        if not self.start_time:
            return 0.0

        end = self.end_time if self.end_time else datetime.now()
        return (end - self.start_time).total_seconds()

    def get_status(self) -> Dict[str, Any]:
        """
        Get complete status dictionary
        """
        with self._lock:
            eta = self.get_eta()

            return {
                "task_id": self.task_id,
                "progress": self.get_progress(),
                "current_step": self.current_step,
                "total_steps": self.total_steps,
                "message": self.message,
                "details": self.details,
                "is_completed": self.is_completed,
                "is_failed": self.is_failed,
                "elapsed_time": self.get_elapsed_time(),
                "eta": eta,
                "eta_human": self._format_eta(eta),
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "end_time": self.end_time.isoformat() if self.end_time else None,
            }

    def _format_eta(self, seconds: Optional[float]) -> Optional[str]:
        """Format ETA in human-readable format"""
        if not seconds:
            return None

        if seconds < 60:
            return f"{int(seconds)} seconds"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f"{minutes} minute{'s' if minutes > 1 else ''}"
        else:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            return f"{hours}h {minutes}m"

    def register_callback(self, callback: Callable):
        """Register a progress callback"""
        self.callbacks.append(callback)

    def reset(self, total_steps: Optional[int] = None):
        """Reset the tracker"""
        with self._lock:
            if total_steps:
                self.total_steps = total_steps
            self.current_step = 0
            self.start_time = None
            self.end_time = None
            self.is_completed = False
            self.is_failed = False
            self.message = ""
            self.details = {}
            self.progress_history.clear()


class ProgressManager:
    """
    Manages multiple progress trackers
    """

    def __init__(self):
        self.trackers: Dict[str, ProgressTracker] = {}
        self._lock = threading.Lock()

    def create_tracker(self, task_id: str, total_steps: int = 100) -> ProgressTracker:
        """Create a new progress tracker"""
        with self._lock:
            tracker = ProgressTracker(task_id, total_steps)
            self.trackers[task_id] = tracker
            return tracker

    def get_tracker(self, task_id: str) -> Optional[ProgressTracker]:
        """Get tracker by task ID"""
        with self._lock:
            return self.trackers.get(task_id)

    def remove_tracker(self, task_id: str):
        """Remove a tracker"""
        with self._lock:
            if task_id in self.trackers:
                del self.trackers[task_id]

    def cleanup_old_trackers(self, max_age_minutes: int = 60):
        """Remove trackers older than max_age_minutes"""
        cutoff = datetime.now() - timedelta(minutes=max_age_minutes)

        with self._lock:
            to_remove = []
            for task_id, tracker in self.trackers.items():
                if tracker.start_time and tracker.start_time < cutoff:
                    to_remove.append(task_id)

            for task_id in to_remove:
                del self.trackers[task_id]

            logger.info(f"Cleaned up {len(to_remove)} old progress trackers")
