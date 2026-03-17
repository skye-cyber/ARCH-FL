import uuid
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable
from threading import Lock
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from ..core.executor import Executor
from ..models.experiment import (
    ExperimentModel,
    ExperimentStatus,
    ExperimentPriority,
    ExperimentSummary,
    ExperimentFilter,
)
from ..utils.logger import logger
from backend.services.websocket_manager import websocketmanager
from backend.core.db import dbmanager, DatabaseManager
from backend.config.settings import settings


class ExperimentManager:
    """
    Manages task creation, storage, and lifecycle with async support
    """

    def __init__(
        self,
        storage_path: Optional[str] = settings.TASK_DIR,
        db_manager: DatabaseManager = dbmanager,
        max_workers: int = 4,
    ):
        self.tasks: Dict[str, ExperimentModel] = {}
        self.executor = Executor(db_manager)
        self._lock = Lock()
        self._async_lock = asyncio.Lock()
        self.storage_path = storage_path
        self.db_manager = db_manager
        self.thread_pool = ThreadPoolExecutor(max_workers=max_workers)
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.task_callbacks: Dict[str, List[Callable]] = {}

        if storage_path:
            Path(storage_path).mkdir(parents=True, exist_ok=True)
            self._load_tasks()

    async def create_task_async(
        self,
        params: Dict[str, Any],
        operation: str = "run_experiment",
        priority: ExperimentPriority = ExperimentPriority.MEDIUM,
        user_id: Optional[str] = None,
    ) -> str:
        """
        Create a new task and start execution asynchronously
        """
        task = ExperimentModel(
            task_id=str(uuid.uuid4()),
            task_type=operation,  # self._determine_task_type(operation),
            operation=operation,
            params=params,
            config={"priority": priority, "user_id": user_id},
            created_at=datetime.now(),
            status=ExperimentStatus.PENDING,
        )

        async with self._async_lock:
            self.tasks[task.task_id] = task

        # Save to disk if storage enabled
        await self._save_task_async(task)

        # Send WebSocket notification
        await websocketmanager.broadcast_to_task(
            f"user_{user_id}" if user_id else "all",
            {
                "type": "task_created",
                "task_id": task.task_id,
                "operation": operation,
                "status": task.status,
                "timestamp": datetime.now().isoformat(),
            },
        )

        # Start async execution
        asyncio.create_task(self._execute_task_async(task))

        logger.info(
            f"Created task {task.task_id} for operation {operation} with priority {priority}"
        )
        return task.task_id

    async def _execute_task_async(self, task: ExperimentModel):
        """
        Execute task asynchronously with proper lifecycle management
        """
        try:
            # Update task status
            task.status = ExperimentStatus.RUNNING
            task.started_at = datetime.now()
            await self._save_task_async(task)

            # Send started notification
            await websocketmanager.broadcast_to_task(
                f"task_{task.task_id}",
                {
                    "type": "task_started",
                    "task_id": task.task_id,
                    "timestamp": datetime.now().isoformat(),
                },
            )

            # Create progress callback
            async def progress_callback(progress: int, message: str, data: dict = None):
                task.progress = progress
                task.message = message
                if data:
                    task.metadata.update(data)
                print("updating:", message, data)

                # Send progress update via WebSocket
                await websocketmanager.send_progress_update(
                    f"task_{task.task_id}",
                    progress,
                    message,
                    data or {},
                )

                # Save task state
                await self._save_task_async(task)

            # Execute the task in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.thread_pool,
                self._execute_task_sync,
                task,
                progress_callback,
            )

            # Handle successful completion
            task.status = ExperimentStatus.COMPLETED
            task.result = result
            task.completed_at = datetime.now()
            task.progress = 100

            await self._save_task_async(task)

            # Send completion notification
            await websocketmanager.send_task_completed(
                f"task_{task.task_id}",
                {
                    "task_id": task.task_id,
                    "result": result,
                    "timestamp": datetime.now().isoformat(),
                },
            )

            # Trigger callbacks
            await self._trigger_callbacks(task.task_id, True, result)

            logger.info(f"Task {task.task_id} completed successfully")

        except asyncio.CancelledError:
            # Handle task cancellation
            task.status = ExperimentStatus.CANCELLED
            task.message = "Task cancelled by user"
            task.completed_at = datetime.now()
            await self._save_task_async(task)

            await websocketmanager.send_task_cancelled(f"task_{task.task_id}")

            logger.info(f"Task {task.task_id} was cancelled")

        except Exception as e:
            # Handle task failure
            task.status = ExperimentStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.now()
            await self._save_task_async(task)

            await websocketmanager.send_task_failed(
                f"task_{task.task_id}",
                str(e),
            )

            # Trigger callbacks
            await self._trigger_callbacks(task.task_id, False, e)
            raise
            logger.error(f"Task {task.task_id} failed: {e}")

    def _execute_task_sync(
        self,
        task: ExperimentModel,
        progress_callback: Callable,
    ) -> Any:
        """
        Synchronous task execution (runs in thread pool)
        """
        # Determine task type and execute accordingly
        if task.operation == "run_experiment":
            return self.executor.execute(
                task.params.get("id"),
                task.params,
                progress_callback,
            )
        # elif task.operation == "train_model":
        #     return self._train_model_sync(task.params, progress_callback)
        # elif task.operation == "evaluate_model":
        #     return self._evaluate_model_sync(task.params, progress_callback)
        else:
            raise ValueError(f"Unknown operation: {task.operation}")

    async def cancel_task_async(
        self, task_id: str, user_id: Optional[str] = None
    ) -> bool:
        """
        Cancel a running task asynchronously
        """
        async with self._async_lock:
            task = self.tasks.get(task_id)
            if not task:
                return False

            if task.status not in [ExperimentStatus.PENDING, ExperimentStatus.RUNNING]:
                return False

            # Cancel the asyncio task if it exists
            if task_id in self.running_tasks:
                self.running_tasks[task_id].cancel()
                del self.running_tasks[task_id]

            task.status = ExperimentStatus.CANCELLED
            task.message = "Task cancelled by user"
            task.completed_at = datetime.now()

            await self._save_task_async(task)

            # Send cancellation notification
            await websocketmanager.broadcast_to_task(
                f"task_{task_id}",
                {
                    "type": "task_cancelled",
                    "task_id": task_id,
                    "user_id": user_id,
                    "timestamp": datetime.now().isoformat(),
                },
            )

            logger.info(f"Task {task_id} cancelled by user {user_id}")
            return True

    async def get_task_status_async(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get task status asynchronously
        """
        async with self._async_lock:
            task = self.tasks.get(task_id)
            if not task:
                return None

            return {
                "task_id": task.task_id,
                "task_type": task.task_type,
                "operation": task.operation,
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
                "metadata": task.metadata,
            }

    async def wait_for_task(
        self, task_id: str, timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Wait for a task to complete and return the result
        """
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        # If task is already completed, return immediately
        if task.status in [
            ExperimentStatus.COMPLETED,
            ExperimentStatus.FAILED,
            ExperimentStatus.CANCELLED,
        ]:
            return await self.get_task_status_async(task_id)

        # Wait for completion using asyncio event
        completion_event = asyncio.Event()
        result_container = {}

        async def on_complete(tid: str, success: bool, result: Any):
            if tid == task_id:
                result_container["success"] = success
                result_container["result"] = result
                completion_event.set()

        self.register_callback(task_id, on_complete)

        try:
            await asyncio.wait_for(completion_event.wait(), timeout)
            return await self.get_task_status_async(task_id)
        except asyncio.TimeoutError:
            raise TimeoutError(
                f"Task {task_id} did not complete within {timeout} seconds"
            )
        finally:
            self.unregister_callback(task_id, on_complete)

    def register_callback(self, task_id: str, callback: Callable):
        """
        Register a callback for task completion
        """
        if task_id not in self.task_callbacks:
            self.task_callbacks[task_id] = []
        self.task_callbacks[task_id].append(callback)

    def unregister_callback(self, task_id: str, callback: Callable):
        """
        Unregister a callback
        """
        if task_id in self.task_callbacks:
            self.task_callbacks[task_id].remove(callback)

    async def _trigger_callbacks(self, task_id: str, success: bool, result: Any):
        """
        Trigger all registered callbacks for a task
        """
        if task_id in self.task_callbacks:
            for callback in self.task_callbacks[task_id]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(task_id, success, result)
                    else:
                        callback(task_id, success, result)
                except Exception as e:
                    logger.error(f"Error in callback for task {task_id}: {e}")

    async def list_tasks_async(
        self, filter_params: Optional[ExperimentFilter] = None
    ) -> List[ExperimentSummary]:
        """
        List tasks with optional filtering asynchronously
        """
        tasks = []

        async with self._async_lock:
            for task in self.tasks.values():
                if self._matches_filter(task, filter_params):
                    tasks.append(
                        ExperimentSummary(
                            task_id=task.task_id,
                            task_type=task.task_type,
                            operation=task.operation,
                            status=task.status,
                            progress=task.progress,
                            created_at=task.created_at.isoformat()
                            if task.created_at
                            else None,
                            completed_at=task.completed_at.isoformat()
                            if task.completed_at
                            else None,
                            metadata=task.metadata,
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

    async def delete_task_async(self, task_id: str) -> bool:
        """
        Delete a task from memory and storage asynchronously
        """
        async with self._async_lock:
            if task_id in self.tasks:
                # Cancel if running
                if task_id in self.running_tasks:
                    self.running_tasks[task_id].cancel()
                    del self.running_tasks[task_id]

                del self.tasks[task_id]

                # Delete from storage if enabled
                if self.storage_path:
                    task_file = Path(self.storage_path) / f"{task_id}.json"
                    if task_file.exists():
                        await asyncio.get_event_loop().run_in_executor(
                            None, task_file.unlink
                        )

                logger.info(f"Task {task_id} deleted")
                return True

        return False

    async def cleanup_old_tasks_async(self, days: int = 7) -> int:
        """
        Remove tasks older than specified days asynchronously
        """
        cutoff = datetime.now() - timedelta(days=days)
        to_delete = []

        async with self._async_lock:
            for task_id, task in self.tasks.items():
                if task.created_at and task.created_at < cutoff:
                    to_delete.append(task_id)

            for task_id in to_delete:
                if task_id in self.running_tasks:
                    self.running_tasks[task_id].cancel()
                    del self.running_tasks[task_id]
                del self.tasks[task_id]

                if self.storage_path:
                    task_file = Path(self.storage_path) / f"{task_id}.json"
                    if task_file.exists():
                        await asyncio.get_event_loop().run_in_executor(
                            None, task_file.unlink
                        )

        logger.info(f"Cleaned up {len(to_delete)} old tasks")
        return len(to_delete)

    async def get_statistics_async(self) -> Dict[str, Any]:
        """
        Get task statistics asynchronously
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
            "min_completion_time": None,
            "max_completion_time": None,
            "success_rate": 0,
        }

        completion_times = []
        successful = 0
        total_completed = 0

        async with self._async_lock:
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
                    total_completed += 1
                    if task.status == ExperimentStatus.COMPLETED:
                        successful += 1

        if completion_times:
            stats["avg_completion_time"] = sum(completion_times) / len(completion_times)
            stats["min_completion_time"] = min(completion_times)
            stats["max_completion_time"] = max(completion_times)

        if total_completed > 0:
            stats["success_rate"] = (successful / total_completed) * 100

        return stats

    async def subscribe_to_task(
        self, task_id: str, websocket, user_id: Optional[str] = None
    ):
        """
        Subscribe a WebSocket connection to task updates
        """
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        # Connect to task-specific WebSocket channel
        await websocketmanager.connect(websocket, f"task_{task_id}", user_id)

        # Send current task state
        await websocketmanager.send_message(
            websocket,
            {
                "type": "task_state",
                "task_id": task_id,
                "status": task.status,
                "progress": task.progress,
                "message": task.message,
                "metadata": task.metadata,
                "timestamp": datetime.now().isoformat(),
            },
        )

    async def _save_task_async(self, task: ExperimentModel):
        """
        Save task to disk asynchronously if storage is enabled
        """
        if not self.storage_path:
            return

        try:
            task_file = Path(self.storage_path) / f"{task.task_id}.json"
            task_dict = task.dict()

            # Convert datetime objects to strings
            if task_dict.get("created_at"):
                task_dict["created_at"] = task_dict["created_at"].isoformat()
            if task_dict.get("started_at"):
                task_dict["started_at"] = task_dict["started_at"].isoformat()
            if task_dict.get("completed_at"):
                task_dict["completed_at"] = task_dict["completed_at"].isoformat()

            # Run file write in thread pool
            await asyncio.get_event_loop().run_in_executor(
                self.thread_pool,
                self._write_task_file,
                task_file,
                task_dict,
            )
        except Exception as e:
            logger.error(f"Failed to save task {task.task_id}: {e}")

    def _write_task_file(self, task_file: Path, task_dict: dict):
        """
        Write task to file (runs in thread pool)
        """
        with open(task_file, "w") as f:
            json.dump(task_dict, f, indent=2)

    def _load_tasks(self):
        """
        Load tasks from disk on startup (runs synchronously)
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

    def _determine_task_type(self, operation: str) -> str:
        """
        Determine task type from operation string
        """
        operation_map = {
            "run_experiment": "experiment",
            "train_model": "training",
            "evaluate_model": "evaluation",
            "export_model": "export",
            "import_model": "import",
            "validate_data": "validation",
            "preprocess_data": "preprocessing",
        }
        return operation_map.get(operation, "unknown")

    def _train_model_sync(
        self, params: Dict[str, Any], progress_callback: Callable
    ) -> Any:
        """
        Synchronous model training
        """
        # Implement model training logic
        progress_callback(0, "Starting model training...")
        # ... training logic ...
        progress_callback(100, "Model training completed")
        return {"status": "success", "model_id": params.get("model_id")}

    def _evaluate_model_sync(
        self, params: Dict[str, Any], progress_callback: Callable
    ) -> Any:
        """
        Synchronous model evaluation
        """
        progress_callback(0, "Starting model evaluation...")
        # ... evaluation logic ...
        progress_callback(100, "Model evaluation completed")
        return {"status": "success", "metrics": {}}

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
            and task.created_at
            and task.created_at < filter_params.created_after
        ):
            return False

        if (
            filter_params.created_before
            and task.created_at
            and task.created_at > filter_params.created_before
        ):
            return False

        # Filter by user if specified
        if (
            filter_params.user_id
            and task.config.get("user_id") != filter_params.user_id
        ):
            return False

        return True

    def __del__(self):
        """
        Cleanup thread pool on deletion
        """
        self.thread_pool.shutdown(wait=False)


experimentmanager = ExperimentManager()
