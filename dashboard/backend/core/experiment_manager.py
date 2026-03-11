import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from threading import Lock
from pathlib import Path
from ..core.executor import Executor
from ..models.experiment import (
    ExperimentModel,
    ExperimentStatus,
    ExperimentPriority,
    ExperimentSummary,
    ExperimentFilter,
)
from ..utils.logger import logger


class ExperimentManager:
    """
    Manages task creation, storage, and lifecycle
    """

    def __init__(
        self, storage_path: Optional[str] = None, filewarp_path: Optional[str] = None
    ):
        self.tasks: Dict[str, ExperimentModel] = {}
        self.executor = Executor(filewarp_path)
        self._lock = Lock()
        self.storage_path = storage_path

        if storage_path:
            Path(storage_path).mkdir(parents=True, exist_ok=True)
            self._load_tasks()

    def create_task(
        self,
        operation: str,
        params: Dict[str, Any],
        priority: ExperimentPriority = ExperimentPriority.MEDIUM,
    ) -> str:
        """
        Create a new task and start execution
        """
        task = ExperimentModel(
            task_id=str(uuid.uuid4()),
            task_type=self._determine_task_type(operation),
            operation=operation,
            params=params,
            config={"priority": priority},
        )

        with self._lock:
            self.tasks[task.task_id] = task

        # Start async execution
        self.executor.execute_async(task, self._on_task_complete)

        # Save to disk if storage enabled
        self._save_task(task)

        logger.info(f"Created task {task.task_id} for operation {operation}")
        return task.task_id

    def _on_task_complete(self, task_id: str, success: bool, result: Any):
        """
        Callback for task completion
        """
        with self._lock:
            task = self.tasks.get(task_id)
            if task:
                task.completed_at = datetime.now()
                if not success:
                    task.status = ExperimentStatus.FAILED
                    task.error = str(result)
                self._save_task(task)

        logger.info(
            f"Task {task_id} completed with status: {task.status if task else 'unknown'}"
        )

    def get_task(self, task_id: str) -> Optional[ExperimentModel]:
        """
        Get task by ID
        """
        with self._lock:
            return self.tasks.get(task_id)

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get task status as dictionary for API response
        """
        task = self.get_task(task_id)
        if not task:
            return None

        return {
            "task_id": task.task_id,
            "status": task.status,
            "progress": task.progress,
            "message": task.message,
            "logs": task.logs[-50:],  # Last 50 logs
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat()
            if task.completed_at
            else None,
            "result": task.result,
            "error": task.error,
        }

    def list_tasks(
        self, filter_params: Optional[ExperimentFilter] = None
    ) -> List[ExperimentSummary]:
        """
        List tasks with optional filtering
        """
        tasks = []

        with self._lock:
            for task in self.tasks.values():
                if self._matches_filter(task, filter_params):
                    tasks.append(
                        ExperimentSummary(
                            task_id=task.task_id,
                            task_type=task.task_type,
                            operation=task.operation,
                            status=task.status,
                            progress=task.progress,
                            created_at=task.created_at.isoformat(),
                            completed_at=task.completed_at.isoformat()
                            if task.completed_at
                            else None,
                        )
                    )

        # Sort by created_at descending (newest first)
        tasks.sort(key=lambda x: x.created_at, reverse=True)

        # Apply pagination
        if filter_params:
            start = filter_params.offset
            end = start + filter_params.limit
            tasks = tasks[start:end]

        return tasks

    def _matches_filter(
        self, task: ExperimentModel, filter_params: Optional[ExperimentFilter]
    ) -> bool:
        """
        Check if task matches filter criteria
        """
        if not filter_params:
            return True

        if filter_params.status and task.status not in filter_params.status:
            return False

        if filter_params.task_type and task.task_type != filter_params.task_type:
            return False

        if filter_params.operation and task.operation != filter_params.operation:
            return False

        if (
            filter_params.created_after
            and task.created_at < filter_params.created_after
        ):
            return False

        if (
            filter_params.created_before
            and task.created_at > filter_params.created_before
        ):
            return False

        return True

    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a running task
        """
        task = self.get_task(task_id)
        if not task:
            return False

        if task.status not in [ExperimentStatus.PENDING, ExperimentStatus.RUNNING]:
            return False

        # Try to cancel via executor
        cancelled = self.executor.cancel_task(task_id)

        if cancelled:
            task.status = ExperimentStatus.CANCELLED
            task.message = "Task cancelled by user"
            task.completed_at = datetime.now()
            self._save_task(task)
            logger.info(f"Task {task_id} cancelled")

        return cancelled

    def delete_task(self, task_id: str) -> bool:
        """
        Delete a task from memory and storage
        """
        with self._lock:
            if task_id in self.tasks:
                del self.tasks[task_id]

                # Delete from storage if enabled
                if self.storage_path:
                    task_file = Path(self.storage_path) / f"{task_id}.json"
                    if task_file.exists():
                        task_file.unlink()

                logger.info(f"Task {task_id} deleted")
                return True

        return False

    def cleanup_old_tasks(self, days: int = 7):
        """
        Remove tasks older than specified days
        """
        cutoff = datetime.now() - timedelta(days=days)
        to_delete = []

        with self._lock:
            for task_id, task in self.tasks.items():
                if task.created_at < cutoff:
                    to_delete.append(task_id)

            for task_id in to_delete:
                del self.tasks[task_id]

                if self.storage_path:
                    task_file = Path(self.storage_path) / f"{task_id}.json"
                    if task_file.exists():
                        task_file.unlink()

        logger.info(f"Cleaned up {len(to_delete)} old tasks")
        return len(to_delete)

    def _determine_task_type(self, operation: str) -> str:
        """
        Determine task type from operation string
        To be Implemented
        """
        pass

    def _save_task(self, task: ExperimentModel):
        """
        Save task to disk if storage is enabled
        """
        if not self.storage_path:
            return

        try:
            task_file = Path(self.storage_path) / f"{task.task_id}.json"
            with open(task_file, "w") as f:
                # Convert to dict for JSON serialization
                task_dict = task.dict()
                # Convert datetime objects to strings
                if task_dict.get("created_at"):
                    task_dict["created_at"] = task_dict["created_at"].isoformat()
                if task_dict.get("started_at"):
                    task_dict["started_at"] = task_dict["started_at"].isoformat()
                if task_dict.get("completed_at"):
                    task_dict["completed_at"] = task_dict["completed_at"].isoformat()

                json.dump(task_dict, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save task {task.task_id}: {e}")

    def _load_tasks(self):
        """
        Load tasks from disk on startup
        """
        if not self.storage_path:
            return

        try:
            storage_dir = Path(self.storage_path)
            for task_file in storage_dir.glob("*.json"):
                try:
                    with open(task_file, "r") as f:
                        task_dict = json.load(f)

                    # Parse datetime strings back to datetime objects
                    if task_dict.get("created_at"):
                        task_dict["created_at"] = datetime.fromisoformat(
                            task_dict["created_at"]
                        )
                    if task_dict.get("started_at"):
                        task_dict["started_at"] = datetime.fromisoformat(
                            task_dict["started_at"]
                        )
                    if task_dict.get("completed_at"):
                        task_dict["completed_at"] = datetime.fromisoformat(
                            task_dict["completed_at"]
                        )

                    task = ExperimentModel(**task_dict)
                    self.tasks[task.task_id] = task

                except Exception as e:
                    logger.error(f"Failed to load task from {task_file}: {e}")

            logger.info(f"Loaded {len(self.tasks)} tasks from storage")
        except Exception as e:
            logger.error(f"Failed to load tasks from storage: {e}")

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get task statistics
        """
        stats = {
            "total": len(self.tasks),
            "pending": 0,
            "running": 0,
            "completed": 0,
            "failed": 0,
            "cancelled": 0,
            "by_type": {},
            "avg_completion_time": None,
        }

        completion_times = []

        with self._lock:
            for task in self.tasks.values():
                # Count by status
                stats[task.status] = stats.get(task.status, 0) + 1

                # Count by type
                stats["by_type"][task.task_type] = (
                    stats["by_type"].get(task.task_type, 0) + 1
                )

                # Calculate completion time
                if task.completed_at and task.started_at:
                    completion_time = (
                        task.completed_at - task.started_at
                    ).total_seconds()
                    completion_times.append(completion_time)

        if completion_times:
            stats["avg_completion_time"] = sum(completion_times) / len(completion_times)
            stats["min_completion_time"] = min(completion_times)
            stats["max_completion_time"] = max(completion_times)

        return stats
