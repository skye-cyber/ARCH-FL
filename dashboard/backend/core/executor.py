import json
import threading
import traceback
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from fastapi import HTTPException
from ..models.experiment import ExperimentModel, ExperimentStatus
from ..utils.logger import logger
from ..core.db import dbmanager


class Executor:
    """
    Executes operations with proper error handling and progress tracking
    """

    def __init__(self, db_manager=None):
        self.active_tasks = {}
        self._lock = threading.Lock()
        self.db_manager = db_manager or dbmanager

    def execute(
        self,
        experiment_id: int,
        experiment_data: Dict[str, Any],
        progress_callback: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """
        Execute an experiment with proper error handling and progress tracking

        Args:
            experiment_id: ID of the experiment in database
            experiment_data: Experiment data from database
            progress_callback: Optional callback for progress updates

        Returns:
            Dictionary with execution results
        """
        try:
            # Validate experiment exists and is in correct state
            if not self.db_manager.validate_experiment_exists(experiment_id):
                raise HTTPException(status_code=404, detail="Experiment not found")

            # Check if experiment is already running
            if experiment_data.get("status") == "running":
                raise HTTPException(
                    status_code=400, detail="Experiment is already running"
                )

            # Validate architecture and dataset exist
            if not self.db_manager.validate_architecture_exists(
                experiment_data["architecture_name"]
            ):
                raise HTTPException(
                    status_code=400,
                    detail=f"Architecture '{experiment_data['architecture_name']}' not found",
                )

            if not self.db_manager.validate_dataset_exists(
                experiment_data["dataset_name"]
            ):
                raise HTTPException(
                    status_code=400,
                    detail=f"Dataset '{experiment_data['dataset_name']}' not found",
                )

            # Update experiment status to running
            with self.db_manager.transaction() as cursor:
                cursor.execute(
                    "UPDATE experiments SET status = ?, updated_at = ? WHERE id = ?",
                    ("running", datetime.now().isoformat(), experiment_id),
                )

            # Create wrapped progress callback
            def wrapped_progress(
                progress: int, message: str, metadata: Optional[Dict] = None
            ):
                """Wrapper to handle progress updates"""
                # Update in database
                with self.db_manager.transaction() as cursor:
                    cursor.execute(
                        "UPDATE experiments SET status = ?, message = ? WHERE id = ?",
                        ("running", message, experiment_id),
                    )

                # Call external callback if provided
                if progress_callback:
                    progress_callback(progress, message, metadata)

            # Execute the experiment
            result = self._execute_experiment(
                experiment_id, experiment_data, wrapped_progress
            )

            # Update final status
            with self.db_manager.transaction() as cursor:
                cursor.execute(
                    "UPDATE experiments SET status = ?, message = ?, updated_at = ? WHERE id = ?",
                    (
                        "completed",
                        "Experiment completed successfully",
                        datetime.now().isoformat(),
                        experiment_id,
                    ),
                )

            return result

        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            # Log the error
            error_msg = f"Experiment failed: {str(e)}"
            logger.error(error_msg)
            logger.debug(traceback.format_exc())

            # Update experiment status to failed
            try:
                with self.db_manager.transaction() as cursor:
                    cursor.execute(
                        "UPDATE experiments SET status = ?, message = ?, error = ?, updated_at = ? WHERE id = ?",
                        (
                            "failed",
                            error_msg,
                            str(e),
                            datetime.now().isoformat(),
                            experiment_id,
                        ),
                    )
            except Exception as db_error:
                logger.error(f"Failed to update experiment status: {db_error}")

            # Re-raise for task manager to handle
            raise

    def _execute_experiment(
        self,
        experiment_id: int,
        experiment_data: Dict[str, Any],
        progress_callback: Callable,
    ) -> Dict[str, Any]:
        """
        Internal method to execute experiment using ARCH-FL core

        Args:
            experiment_id: ID of the experiment
            experiment_data: Experiment data from database
            progress_callback: Callback for progress updates

        Returns:
            Dictionary with execution results
        """
        try:
            # Import ARCH-FL core components
            from src.core.dashboard_integration import DashboardConnector
            from src.models.architecture_registry import get_architecture_registry
            from src.data.loader_registry import get_data_loader_registry
            from src.core.coordinator import Coordinator

            # from src.training.fedavg import federated_average Not found
            from src.training.fedavg import FederatedTrainer
            from src.training.local_trainer import LocalTrainer

            # Initialize dashboard connector
            dashboard_connector = DashboardConnector()
            # Below hooks should be used appropriately- Note dashboard may handle some of fubctionlaities so check db record
            # dashboard_connector.create_experiment_record() do nothing is exists
            # dashboard_connector.add_experiment_result()
            # dashboard_connector.update_experiment_status()

            # Get architecture and dataset
            arch_registry = get_architecture_registry()
            data_registry = get_data_loader_registry()

            # Get architecture info
            architecture_info = arch_registry.get_architecture_info(
                experiment_data["architecture_name"]
            )
            if not architecture_info:
                raise ValueError(
                    f"Architecture '{experiment_data['architecture_name']}' not found in registry"
                )

            # Get dataset info
            dataset_info = data_registry.get_dataset_info(
                experiment_data["dataset_name"]
            )
            if not dataset_info:
                raise ValueError(
                    f"Dataset '{experiment_data['dataset_name']}' not found in registry"
                )

            # Create model
            model = arch_registry.create_model(
                experiment_data["architecture_name"],
                input_size=dataset_info.get("input_size", 28),
            )

            # Create coordinator with callback
            coordinator = Coordinator(
                model,
                aggregation_method=experiment_data["parameters"].get(
                    "aggregation_method", "fed_avg"
                ),
                progress_callback=lambda progress, message, metadata=None: (
                    progress_callback(progress, message, metadata)
                ),
            )

            # Get training parameters
            params = json.loads(experiment_data["parameters"])
            num_rounds = params.get("num_rounds", 5)
            num_clients = experiment_data["num_clients"]

            # Report initial progress
            progress_callback(0, "Starting federated training")

            # Run federated training Needs fixing
            federated_average(
                coordinator=coordinator,
                dataset_name=experiment_data["dataset_name"],
                num_clients=num_clients,
                num_rounds=num_rounds,
                iid=experiment_data["iid"],
                progress_callback=lambda progress, message, metadata=None: (
                    progress_callback(progress, message, metadata)
                ),
            )

            # Report completion
            progress_callback(100, "Training completed successfully")

            # Update final status in database
            with self.db_manager.transaction() as cursor:
                cursor.execute(
                    "UPDATE experiments SET status = ?, message = ?, updated_at = ? WHERE id = ?",
                    (
                        "completed",
                        "Training completed successfully",
                        datetime.now().isoformat(),
                        experiment_id,
                    ),
                )

            return {
                "status": "completed",
                "message": "Experiment completed successfully",
                "experiment_id": experiment_id,
                "rounds_completed": num_rounds,
            }

        except ImportError as e:
            # Fallback if ARCH-FL core not available
            error_msg = f"ARCH-FL core not available: {e}"
            logger.error(error_msg)

            # Update status to failed
            with self.db_manager.transaction() as cursor:
                cursor.execute(
                    "UPDATE experiments SET status = ?, message = ?, error = ?, updated_at = ? WHERE id = ?",
                    (
                        "failed",
                        error_msg,
                        error_msg,
                        datetime.now().isoformat(),
                        experiment_id,
                    ),
                )

            raise RuntimeError(error_msg)
        except Exception as e:
            error_msg = f"Experiment execution failed: {str(e)}"
            logger.error(error_msg)
            logger.debug(traceback.format_exc())

            # Update status to failed
            with self.db_manager.transaction() as cursor:
                cursor.execute(
                    "UPDATE experiments SET status = ?, message = ?, error = ?, updated_at = ? WHERE id = ?",
                    (
                        "failed",
                        error_msg,
                        str(e),
                        datetime.now().isoformat(),
                        experiment_id,
                    ),
                )

            raise RuntimeError(error_msg)

    def execute_async(
        self,
        experiment_id: int,
        experiment_data: Dict[str, Any],
        callback: Optional[Callable] = None,
    ):
        """
        Execute an experiment asynchronously in a separate thread

        Args:
            experiment_id: ID of the experiment
            experiment_data: Experiment data from database
            callback: Optional callback for completion notification

        Returns:
            Thread object
        """

        def _execute_wrapper():
            try:
                with self._lock:
                    self.active_tasks[experiment_id] = experiment_data

                result = self.execute(experiment_id, experiment_data)

                if callback:
                    callback(experiment_id, True, result)

            except Exception as e:
                if callback:
                    callback(experiment_id, False, str(e))
            finally:
                with self._lock:
                    if experiment_id in self.active_tasks:
                        del self.active_tasks[experiment_id]

        thread = threading.Thread(target=_execute_wrapper)
        thread.daemon = True
        thread.start()

        return thread

    def cancel_task(self, experiment_id: int) -> bool:
        """
        Attempt to cancel a running experiment

        Args:
            experiment_id: ID of the experiment to cancel

        Returns:
            True if cancellation was initiated, False otherwise
        """
        with self._lock:
            if experiment_id in self.active_tasks:
                # Update status in database
                with self.db_manager.transaction() as cursor:
                    cursor.execute(
                        "UPDATE experiments SET status = ?, message = ?, updated_at = ? WHERE id = ?",
                        (
                            "cancelled",
                            "Experiment cancelled by user",
                            datetime.now().isoformat(),
                            experiment_id,
                        ),
                    )

                # Remove from active tasks
                del self.active_tasks[experiment_id]

                return True
        return False

    def get_active_tasks(self) -> Dict[int, Dict[str, Any]]:
        """
        Get all currently active experiments

        Returns:
            Dictionary of active experiments
        """
        with self._lock:
            return self.active_tasks.copy()
