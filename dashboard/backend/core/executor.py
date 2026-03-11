import json
import threading
import traceback
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from ..models.experiment import ExperimentModel, ExperimentStatus
from ..utils.logger import logger
from ..core.db import dbmanager


class Executor:
    """
    Executes operations with proper error handling and progress tracking
    """

    def __init__(self, filewarp_path: Optional[str] = None):
        self.active_tasks = {}
        self._lock = threading.Lock()

    def execute(
        self, task: ExperimentModel, progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Execute a task and return the result
        """
        try:
            # Get the appropriate handler
            # Here we do not need interpreter we just call the experiment executor

            # Create wrapped progress callback
            def wrapped_progress(progress: int, message: str):
                task.progress = progress
                task.message = message
                task.logs.append(f"[{datetime.now().isoformat()}] {message}")
                if progress_callback:
                    progress_callback(progress, message)

            # Execute the handler
            result = handler(task.params, wrapped_progress)
            # Get experiment details
            conn = dbmanager.connection
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM experiments WHERE id = ?", (experiment_id,))
            experiment = cursor.fetchone()
            conn.close()

            if not experiment:
                raise HTTPException(status_code=404, detail="Experiment not found")

            experiment_dict = dict(experiment)

            # Check if experiment is already running
            if experiment_dict["status"] == "running":
                raise HTTPException(
                    status_code=400, detail="Experiment is already running"
                )

            # Update task with result
            task.result = result
            task.status = ExperimentStatus.COMPLETED
            task.progress = 100
            task.message = "Operation completed successfully"

            return result

        except Exception as e:
            # Log the error
            error_msg = f"Operation failed: {str(e)}"
            logger.error(error_msg)
            logger.debug(traceback.format_exc())

            # Update task with error
            task.status = ExperimentStatus.FAILED
            task.error = error_msg
            task.message = error_msg
            task.logs.append(f"[{datetime.now().isoformat()}] ERROR: {error_msg}")

            # Re-raise for task manager to handle
            raise

    def execute_experiment(experiment: Dict):
        try:
            # Import ARCH-FL core components
            from src.core.dashboard_integration import (
                DashboardConnector,
                create_dashboard_callback,
            )
            from src.models.architecture_registry import get_architecture_registry
            from src.data.loader_registry import get_data_loader_registry
            from src.core.coordinator import Coordinator
            from src.training.fedavg import federated_average

            # Initialize dashboard connector
            dashboard_connector = DashboardConnector()

            # Create progress callback
            progress_callback = create_dashboard_callback(
                experiment_id, dashboard_connector
            )

            # Get architecture and dataset
            try:
                arch_registry = get_architecture_registry()
                data_registry = get_data_loader_registry()

                # Get architecture
                architecture_info = arch_registry.get_architecture_info(
                    experiment["architecture_name"]
                )

                # Get dataset
                dataset_info = data_registry.get_dataset_info(
                    experiment["dataset_name"]
                )

                # Create model
                model = arch_registry.create_model(
                    experiment["architecture_name"],
                    input_size=dataset_info.get("input_size", 28),
                )

                # Create coordinator with callback
                coordinator = Coordinator(
                    model,
                    aggregation_method=experiment["parameters"].get(
                        "aggregation_method", "fed_avg"
                    ),
                    progress_callback=progress_callback,
                )

                # Get training parameters
                params = json.loads(experiment["parameters"])
                num_rounds = params.get("num_rounds", 5)
                num_clients = experiment["num_clients"]

                # Run federated training
                federated_average(
                    coordinator=coordinator,
                    dataset_name=experiment["dataset_name"],
                    num_clients=num_clients,
                    num_rounds=num_rounds,
                    iid=experiment["iid"],
                    progress_callback=progress_callback,
                )

                # Update final status
                dashboard_connector.update_experiment_status(
                    experiment_id,
                    "completed",
                    {"round": num_rounds, "status": "completed"},
                )

            except ImportError as e:
                # Fallback if ARCH-FL core not available
                print(f"ARCH-FL core not available: {e}")
                dashboard_connector.update_experiment_status(
                    experiment_id, "failed", {"error": "ARCH-FL core not available"}
                )
            except Exception as e:
                print(f"Experiment failed: {e}")
                dashboard_connector.update_experiment_status(
                    experiment_id, "failed", {"error": str(e)}
                )

        except Exception as e:
            print(f"Error in experiment execution: {e}")

    def execute_async(self, task: ExperimentModel, callback: Optional[Callable] = None):
        """
        Execute a task asynchronously in a separate thread
        """

        def _execute_wrapper():
            try:
                with self._lock:
                    self.active_tasks[task.task_id] = task

                result = self.execute(task)

                if callback:
                    callback(task.task_id, True, result)

            except Exception as e:
                if callback:
                    callback(task.task_id, False, str(e))
            finally:
                with self._lock:
                    if task.task_id in self.active_tasks:
                        del self.active_tasks[task.task_id]

        thread = threading.Thread(target=_execute_wrapper)
        thread.daemon = True
        thread.start()

        return thread

    def cancel_task(self, task_id: str) -> bool:
        """
        Attempt to cancel a running task
        """
        with self._lock:
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                task.cancel_flag = True
                task.status = ExperimentStatus.CANCELLED
                task.message = "Task cancelled by user"
                return True
        return False

    def get_active_tasks(self) -> Dict[str, ExperimentModel]:
        """
        Get all currently active tasks
        """
        with self._lock:
            return self.active_tasks.copy()
