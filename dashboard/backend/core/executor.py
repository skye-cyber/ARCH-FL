import json
import threading
import traceback
from tqdm.auto import tqdm
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from fastapi import HTTPException

# from ..models.experiment import ExperimentStatus
from ..utils.logger import logger
from ..core.db import dbmanager

# from backend.services.websocket_manager import websocketmanager


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
            if not experiment_id:
                raise HTTPException(
                    status_code=404, detail="Experiment id was not provided"
                )
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
                print(type(progress), type(message), type(metadata))
                """Wrapper to handle progress updates"""
                # Update in database
                with self.db_manager.transaction() as cursor:
                    cursor.execute(
                        "UPDATE experiments SET status = ?, message = ? WHERE id = ?",
                        (
                            "running",
                            message,
                            experiment_id,
                        ),
                    )

                # Call external callback if provided
                if progress_callback:
                    progress_callback(progress, message, metadata)

            # Execute the experiment
            result = self._execute_experiment(
                experiment_id,
                experiment_data,  # wrapped_progress
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
        progress_callback: Callable = None,
    ) -> Dict[str, Any]:
        """
        Internal method to execute experiment using ARCH-FL core

        This method implements the complete experiment lifecycle:
        1. Register architecture and dataset if not already registered
        2. Local training (if enabled)
        3. Federated training with aggregation
        4. Metrics collection and reporting

        Args:
            experiment_id: ID of the experiment
            experiment_data: Experiment data from database
            progress_callback: Callback for progress updates

        Returns:
            Dictionary with execution results including metrics
        """
        try:
            # Import ARCH-FL core components
            from src.core.dashboard_integration import DashboardConnector
            from src.models.architecture_registry import get_architecture_registry
            from src.data.loader_registry import get_data_loader_registry
            from src.data.registry import get_dataset_registry
            from src.core.coordinator import Coordinator
            from src.training.fedavg import FederatedTrainer
            # from src.training.local_trainer import LocalTrainer

            from src.core.client import Client

            # Initialize dashboard connector
            dashboard_connector = DashboardConnector()

            # Get registries
            arch_registry = get_architecture_registry()
            data_loader_registry = get_data_loader_registry()
            dataset_registry = get_dataset_registry()

            # Register architecture if not already in registry
            if not arch_registry.is_supported(experiment_data["architecture_name"]):
                # Get architecture from database
                with self.db_manager.transaction() as cursor:
                    cursor.execute(
                        "SELECT * FROM architectures WHERE name = ?",
                        (experiment_data["architecture_name"],),
                    )
                    arch_data = cursor.fetchone()

                if arch_data:
                    arch_config = json.loads(arch_data["config"])
                    compatible_datasets = json.loads(
                        arch_data["compatible_datasets"] or "[]"
                    )

                    # Register in architecture registry
                    arch_registry.register_architecture(
                        experiment_data["architecture_name"],
                        arch_config,
                        description=arch_data["description"],
                        compatible_datasets=compatible_datasets,
                    )
                    logger.info(
                        f"Registered architecture '{experiment_data['architecture_name']}' in registry"
                    )
                else:
                    raise ValueError(
                        f"Architecture '{experiment_data['architecture_name']}' not found in database"
                    )

            # Register dataset if not already in registry
            if not dataset_registry.is_supported(experiment_data["dataset_name"]):
                # Get dataset from database
                with self.db_manager.transaction() as cursor:
                    cursor.execute(
                        "SELECT * FROM datasets WHERE name = ?",
                        (experiment_data["dataset_name"],),
                    )
                    dataset_data = cursor.fetchone()

                if dataset_data:
                    dataset_metadata = json.loads(dataset_data["metadata"])

                    # Register in data loader registry
                    data_loader_registry.datasets[experiment_data["dataset_name"]] = {
                        "name": dataset_data["name"],
                        "description": dataset_data["description"],
                        "data_type": dataset_metadata.get("data_type", "chest_xray"),
                        "image_format": dataset_metadata.get(
                            "image_format", "grayscale"
                        ),
                        "default_size": dataset_metadata.get("input_size", [224, 224]),
                        "channels": dataset_metadata.get("channels", 1),
                        "task_types": dataset_metadata.get(
                            "task", ["binary_classification"]
                        ),
                        "path": dataset_metadata.get("location"),
                        "supported": True,
                        "metadata_file": dataset_metadata.get("location"),
                    }
                    logger.info(
                        f"Registered dataset '{experiment_data['dataset_name']}' in registry"
                    )
                else:
                    raise ValueError(
                        f"Dataset '{experiment_data['dataset_name']}' not found in database"
                    )

            # Verify architecture and dataset are now in registries
            if not arch_registry.is_supported(experiment_data["architecture_name"]):
                raise ValueError(
                    f"Failed to register architecture '{experiment_data['architecture_name']}'"
                )

            if not data_loader_registry.is_supported(experiment_data["dataset_name"]):
                raise ValueError(
                    f"The dataset has not registered loader '{experiment_data['dataset_name']}'"
                )

            # Get training parameters
            params = json.loads(experiment_data["parameters"])
            num_rounds = params.get("num_rounds", 5)
            num_clients = experiment_data["num_clients"]
            iid = experiment_data["iid"]
            local_epochs = params.get("local_epochs", 1)
            learning_rate = params.get("learning_rate", 0.01)
            batch_size = params.get("batch_size", 32)

            # Loss function - configurable
            loss_function = params.get("loss_function", "cross_entropy")

            # Privacy parameters
            dp_enabled = params.get("dp_enabled", False)
            epsilon = params.get("epsilon", 1.0)
            delta = params.get("delta", 1e-5)

            # Report initial progress
            if progress_callback:
                progress_callback(0, "Initializing experiment")

            # Create model
            model = arch_registry.create_model_from_architecture(
                experiment_data["architecture_name"],
            )

            # Create data loaders
            client_loaders, test_loader = data_loader_registry.create_data_loaders(
                experiment_data["dataset_name"],
                num_clients,
                iid=iid,
                batch_size=batch_size,
                alpha=params.get("alpha", 0.5),
            )

            # Create clients with proper loss tracking
            clients = []
            for client_id in range(num_clients):
                client_model = arch_registry.create_model_from_architecture(
                    experiment_data["architecture_name"],
                )

                # Initialize client with loss function
                client = Client(
                    client_id,
                    client_model,
                    client_loaders[client_id],
                    "cpu",
                    loss_function=loss_function,  # Pass loss function to client
                )
                clients.append(client)

            # Create coordinator with callback for better metrics
            coordinator = Coordinator(
                model,
                aggregation_method=params.get("aggregation_method", "fed_avg"),
                progress_callback=lambda round_num, metrics, event_type: (
                    progress_callback(
                        int((round_num / num_rounds) * 100),
                        f"Training round {round_num}/{num_rounds}",
                        {"round": round_num, "metrics": metrics, "event": event_type},
                    )
                ),
            )

            # Create federated trainer with loss tracking
            federated_trainer = FederatedTrainer(
                coordinator, clients, test_loader, "cpu", loss_function=loss_function
            )

            # Report progress
            progress_callback(5, "Clients initialized, starting training")

            # Run federated training with proper metrics
            results = {
                "rounds": [],
                "final_accuracy": 0.0,
                "final_loss": 0.0,
                "privacy_spent": None,
            }

            # Track best metrics
            best_accuracy = 0.0
            best_loss = float("inf")

            # Store per-client metrics history
            client_metrics_history = {i: [] for i in range(num_clients)}

            # Update dashboard with round results
            dashboard_connector.update_experiment_status(experiment_id, "running")
            # After starting the experiment
            progress_callback(
                0,
                "Experiment started",
                {
                    "type": "experiment_started",
                    "experiment_id": experiment_id,
                    "timestamp": datetime.now().isoformat(),
                },
            )
            for round_num in tqdm(range(1, num_rounds + 1)):
                # Train clients
                client_indices = list(range(num_clients))

                # Track round metrics
                round_client_accuracies = []
                round_client_losses = []

                # Local training phase with loss tracking
                for client_idx in client_indices:
                    client = clients[client_idx]

                    # Perform local training and get metrics
                    client_update, client_metrics = client.local_train_with_metrics(
                        coordinator.get_global_model(), local_epochs, learning_rate
                    )

                    # Store client update for aggregation
                    clients[client_idx].model.load_state_dict(client_update)

                    # Track client metrics
                    if client_metrics:
                        round_client_accuracies.append(
                            client_metrics.get("accuracy", 0)
                        )
                        round_client_losses.append(client_metrics.get("loss", 0))

                        client_accuracy = client_metrics.get("accuracy", 0)
                        client_loss = client_metrics.get("loss", 0)

                        # Store in history
                        client_metrics_history[client_idx].append(
                            {
                                "round": round_num,
                                "accuracy": client_accuracy,
                                "loss": client_loss,
                            }
                        )
                        # Send client update
                        progress_callback(
                            f"{(round_num / num_rounds) * 100:.2f}",
                            f"Client {client_idx}: Rounds: {round_num} of {num_rounds}",
                            {
                                "type": "client_update",
                                "client_id": client_idx,
                                "round": round_num,
                                "accuracy": client_accuracy,
                                "loss": client_loss,
                                "timestamp": datetime.now().isoformat(),
                            },
                        )

                # Federated aggregation phase
                client_updates = []
                client_sizes = []

                for client_idx in client_indices:
                    client = clients[client_idx]
                    client_updates.append(client.model.state_dict())
                    client_sizes.append(client.get_dataset_size())

                # Aggregate updates
                coordinator.aggregate(client_updates, client_sizes, round_num)

                # Evaluate global model - get both accuracy and loss
                eval_metrics = federated_trainer.evaluate_with_metrics()
                global_accuracy = eval_metrics.get("accuracy", 0)
                global_loss = eval_metrics.get("loss", 0)

                # Update best metrics
                best_accuracy = max(best_accuracy, global_accuracy)
                best_loss = min(best_loss, global_loss)

                # After aggregation, send round completed with metrics
                progress_callback(
                    f"{(round_num / num_rounds) * 100:.2f}",
                    {
                        "type": "round_completed",
                        "round": round_num,
                        "accuracy": global_accuracy,
                        "loss": global_loss,
                        "timestamp": datetime.now().isoformat(),
                    },
                )
                progress = f"{(round_num / num_rounds) * 100:.2f}"
                # Send progress update
                progress_callback(
                    progress,
                    f"Round {round_num}/{num_rounds} completed",
                    {"round": round_num, "accuracy": global_accuracy},
                )
                # Record global round results
                round_result = {
                    "round": round_num,
                    "accuracy": global_accuracy,
                    "loss": global_loss,
                    "num_clients": num_clients,
                    "iid": iid,
                    "aggregation_method": params.get("aggregation_method", "fed_avg"),
                    "epsilon": epsilon if dp_enabled else None,
                    "delta": delta if dp_enabled else None,
                    "best_accuracy_so_far": best_accuracy,
                    "best_loss_so_far": best_loss,
                }

                results["rounds"].append(round_result)

                # Record per-client results
                for client_idx in client_indices:
                    # Get client-specific metrics from history
                    client_metrics = (
                        client_metrics_history[client_idx][-1]
                        if client_metrics_history[client_idx]
                        else {}
                    )

                    client_round_result = {
                        "client_id": client_idx,
                        "round": round_num,
                        "accuracy": client_metrics.get(
                            "accuracy", global_accuracy
                        ),  # Fallback to global if not available
                        "loss": client_metrics.get(
                            "loss", global_loss
                        ),  # Fallback to global if not available
                        "num_clients": num_clients,
                        "iid": iid,
                        "aggregation_method": params.get(
                            "aggregation_method", "fed_avg"
                        ),
                        "epsilon": epsilon if dp_enabled else None,
                        "delta": delta if dp_enabled else None,
                    }

                    # Update clients table with round results
                    dashboard_connector.add_client_result(
                        experiment_id, client_round_result
                    )

                # Calculate progress
                progress = int((round_num / num_rounds) * 95) + 5  # 5-99%
                progress_callback(
                    progress,
                    f"Round {round_num}/{num_rounds} completed - Accuracy: {global_accuracy:.2f}%, Loss: {global_loss:.4f}",
                    {
                        "round": round_num,
                        "accuracy": global_accuracy,
                        "loss": global_loss,
                    },
                )

            # Final evaluation
            final_metrics = federated_trainer.evaluate_with_metrics()
            final_accuracy = final_metrics.get("accuracy", 0)
            final_loss = final_metrics.get("loss", 0)

            results["final_accuracy"] = final_accuracy
            results["final_loss"] = final_loss
            results["best_accuracy"] = best_accuracy
            results["best_loss"] = best_loss

            # Report completion
            progress_callback(100, "Training completed successfully")

            # Store final results
            final_result = {
                "experiment_id": experiment_id,
                "status": "completed",
                "message": "Experiment completed successfully",
                "rounds_completed": num_rounds,
                "final_accuracy": final_accuracy,
                "final_loss": final_loss,
                "best_accuracy": best_accuracy,
                "best_loss": best_loss,
                "num_clients": num_clients,
                "iid": iid,
                "aggregation_method": params.get("aggregation_method", "fed_avg"),
                "dp_enabled": dp_enabled,
                "epsilon": epsilon if dp_enabled else None,
                "delta": delta if dp_enabled else None,
                "total_rounds": len(results["rounds"]),
                "client_metrics_summary": {
                    "total_clients": num_clients,
                    "rounds_per_client": len(client_metrics_history[0])
                    if client_metrics_history
                    else 0,
                },
            }

            # Update dashboard with final results
            dashboard_connector.update_experiment_status(
                experiment_id, "completed", final_result
            )

            return final_result

        except ImportError as e:
            error_msg = f"ARCH-FL core not available: {e}"
            logger.error(error_msg)
            logger.debug(traceback.format_exc())

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

    def _execute_experiment_prev(
        self,
        experiment_id: int,
        experiment_data: Dict[str, Any],
        progress_callback: Callable,
    ) -> Dict[str, Any]:
        """
        Internal method to execute experiment using ARCH-FL core

        This method implements the complete experiment lifecycle:
        1. Register architecture and dataset if not already registered
        2. Local training (if enabled)
        3. Federated training with aggregation
        4. Metrics collection and reporting

        Args:
            experiment_id: ID of the experiment
            experiment_data: Experiment data from database
            progress_callback: Callback for progress updates

        Returns:
            Dictionary with execution results including metrics
        """
        try:
            # Import ARCH-FL core components
            from src.core.dashboard_integration import DashboardConnector
            from src.models.architecture_registry import get_architecture_registry
            from src.data.loader_registry import get_data_loader_registry
            from src.data.registry import get_dataset_registry
            from src.core.coordinator import Coordinator
            from src.training.fedavg import FederatedTrainer
            from src.training.local_trainer import LocalTrainer

            from src.core.client import Client
            import torch

            # Initialize dashboard connector
            dashboard_connector = DashboardConnector()

            # Get registries
            arch_registry = get_architecture_registry()
            data_loader_registry = get_data_loader_registry()
            dataset_registry = get_dataset_registry()

            # Register architecture if not already in registry
            if not arch_registry.is_supported(experiment_data["architecture_name"]):
                # Get architecture from database
                with self.db_manager.transaction() as cursor:
                    cursor.execute(
                        "SELECT * FROM architectures WHERE name = ?",
                        (experiment_data["architecture_name"],),
                    )
                    arch_data = cursor.fetchone()

                if arch_data:
                    arch_config = json.loads(arch_data["config"])
                    compatible_datasets = json.loads(
                        arch_data["compatible_datasets"] or "[]"
                    )

                    # Register in architecture registry
                    arch_registry.register_architecture(
                        experiment_data["architecture_name"],
                        arch_config,
                        description=arch_data["description"],
                        compatible_datasets=compatible_datasets,
                    )
                    logger.info(
                        f"Registered architecture '{experiment_data['architecture_name']}' in registry"
                    )
                else:
                    raise ValueError(
                        f"Architecture '{experiment_data['architecture_name']}' not found in database"
                    )

            # Register dataset if not already in registry
            if not dataset_registry.is_supported(experiment_data["dataset_name"]):
                # Get dataset from database
                with self.db_manager.transaction() as cursor:
                    cursor.execute(
                        "SELECT * FROM datasets WHERE name = ?",
                        (experiment_data["dataset_name"],),
                    )
                    dataset_data = cursor.fetchone()

                if dataset_data:
                    dataset_metadata = json.loads(dataset_data["metadata"])

                    # Register in data loader registry
                    # Note: The registry doesn't have a direct register method,
                    # but we can add it to the internal datasets dict
                    data_loader_registry.datasets[experiment_data["dataset_name"]] = {
                        "name": dataset_data["name"],
                        "description": dataset_data["description"],
                        "data_type": dataset_metadata.get("data_type", "chest_xray"),
                        "image_format": dataset_metadata.get(
                            "image_format", "grayscale"
                        ),
                        "default_size": dataset_metadata.get("input_size", [224, 224]),
                        "channels": dataset_metadata.get("channels", 1),
                        "task_types": dataset_metadata.get(
                            "task", ["binary_classification"]
                        ),
                        "path": dataset_metadata.get("location"),
                        "supported": True,
                        "metadata_file": dataset_metadata.get("location"),
                    }
                    logger.info(
                        f"Registered dataset '{experiment_data['dataset_name']}' in registry"
                    )
                else:
                    raise ValueError(
                        f"Dataset '{experiment_data['dataset_name']}' not found in database"
                    )

            # Verify architecture and dataset are now in registries
            if not arch_registry.is_supported(experiment_data["architecture_name"]):
                raise ValueError(
                    f"Failed to register architecture '{experiment_data['architecture_name']}'"
                )

            if not data_loader_registry.is_supported(experiment_data["dataset_name"]):
                raise ValueError(
                    f"The dataset has not registered loader '{experiment_data['dataset_name']}'"
                )

            # Get training parameters
            params = json.loads(experiment_data["parameters"])
            num_rounds = params.get("num_rounds", 5)
            num_clients = experiment_data["num_clients"]
            iid = experiment_data["iid"]
            local_epochs = params.get("local_epochs", 1)
            learning_rate = params.get("learning_rate", 0.01)

            # Privacy parameters
            dp_enabled = params.get("dp_enabled", False)
            epsilon = params.get("epsilon", 1.0)
            delta = params.get("delta", 1e-5)

            # Report initial progress
            progress_callback(0, "Initializing experiment")

            # Create model
            model = arch_registry.create_model_from_architecture(
                experiment_data["architecture_name"],
                # input_size=dataset_info.get("input_size", 28),
            )

            # Create data loaders
            client_loaders, test_loader = data_loader_registry.create_data_loaders(
                experiment_data["dataset_name"],
                num_clients,
                iid=iid,
                batch_size=params.get("batch_size", 32),
                alpha=params.get("alpha", 0.5),
            )

            # Create clients
            clients = []
            for client_id in range(num_clients):
                client_model = arch_registry.create_model_from_architecture(
                    experiment_data["architecture_name"],
                    # input_size=dataset_info.get("input_size", 28),
                )
                client = Client(
                    client_id, client_model, client_loaders[client_id], "cpu"
                )
                clients.append(client)

            # Create coordinator with callback
            coordinator = Coordinator(
                model,
                aggregation_method=params.get("aggregation_method", "fed_avg"),
                progress_callback=lambda round_num, metrics, event_type: (
                    progress_callback(
                        int((round_num / num_rounds) * 100),
                        f"Training round {round_num}/{num_rounds}",
                        {
                            "round": round_num,
                            "metrics": metrics,
                            "event": event_type,
                        },
                    )
                ),
            )

            # Create federated trainer
            federated_trainer = FederatedTrainer(
                coordinator, clients, test_loader, "cpu"
            )

            # Report progress
            progress_callback(5, "Clients initialized, starting training")

            # Run federated training
            results = {
                "rounds": [],
                "final_accuracy": 0.0,
                "privacy_spent": None,
            }

            # Update dashboard with round results
            dashboard_connector.update_experiment_status(experiment_id, "running")
            for round_num in tqdm(range(1, num_rounds + 1)):
                # Train clients
                client_indices = list(range(num_clients))

                # Local training phase
                for client_idx in client_indices:
                    client = clients[client_idx]
                    client_update = client.local_train(
                        coordinator.get_global_model(), local_epochs, learning_rate
                    )

                    # Store client update for aggregation
                    clients[client_idx].model.load_state_dict(client_update)

                # Federated aggregation phase
                client_updates = []
                client_sizes = []

                for client_idx in client_indices:
                    client = clients[client_idx]
                    client_updates.append(client.model.state_dict())
                    client_sizes.append(client.get_dataset_size())

                # Aggregate updates
                coordinator.aggregate(client_updates, client_sizes, round_num)

                # Evaluate and record results
                accuracy = federated_trainer.evaluate()

                # Record round results
                round_result = {
                    "round": round_num,
                    "accuracy": accuracy,
                    "num_clients": num_clients,
                    "iid": iid,
                    "aggregation_method": params.get("aggregation_method", "fed_avg"),
                    "epsilon": epsilon if dp_enabled else None,
                    "delta": delta if dp_enabled else None,
                }

                results["rounds"].append(round_result)

                # Record round results - update for EACH client individually
                for client_idx in client_indices:
                    client = clients[client_idx]

                    # You might need to get client-specific metrics
                    # This could include loss, accuracy, or other metrics per client
                    client_accuracy = (
                        accuracy  # Or get client-specific accuracy if available
                    )
                    client_loss = (
                        client.get_loss() if hasattr(client, "get_loss") else None
                    )

                    client_round_result = {
                        "client_id": client_idx,  # Add client_id for each client
                        "round": round_num,
                        "accuracy": client_accuracy,
                        "loss": client_loss,
                        "num_clients": num_clients,
                        "iid": iid,
                        "aggregation_method": params.get(
                            "aggregation_method", "fed_avg"
                        ),
                        "epsilon": epsilon if dp_enabled else None,
                        "delta": delta if dp_enabled else None,
                    }

                    # results["rounds"].append(round_result)

                    # Update clients table with round results for THIS client
                    dashboard_connector.add_client_result(
                        experiment_id, client_round_result
                    )

                # Calculate progress
                progress = int((round_num / num_rounds) * 95) + 5  # 5-99%
                progress_callback(
                    progress,
                    f"Round {round_num}/{num_rounds} completed - Accuracy: {accuracy:.2f}%",
                    {"round": round_num, "accuracy": accuracy},
                )

            # Final evaluation
            final_accuracy = federated_trainer.evaluate()
            results["final_accuracy"] = final_accuracy

            # Report completion
            progress_callback(100, "Training completed successfully")

            # Store final results
            final_result = {
                "experiment_id": experiment_id,
                "status": "completed",
                "message": "Experiment completed successfully",
                "rounds_completed": num_rounds,
                "final_accuracy": final_accuracy,
                "num_clients": num_clients,
                "iid": iid,
                "aggregation_method": params.get("aggregation_method", "fed_avg"),
                "dp_enabled": dp_enabled,
                "epsilon": epsilon if dp_enabled else None,
                "delta": delta if dp_enabled else None,
                "rounds": len(results["rounds"]),
                "loss": 0,
            }

            # Update dashboard with final results
            dashboard_connector.update_experiment_status(
                experiment_id, "completed", final_result
            )

            return final_result

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
