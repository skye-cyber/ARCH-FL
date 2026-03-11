import json
from fastapi import APIRouter, HTTPException
from typing import List, Dict
from datetime import datetime
from backend.models.requests import ExperimentCreate, ExperimentUpdate
from backend.core.db import dbmanager


router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.get("/", response_model=List[Dict])
def get_experiments():
    """Get all experiments."""
    conn = dbmanager.connection
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM experiments ORDER BY created_at DESC")
    experiments = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return experiments


@router.post("/", response_model=Dict)
def create_experiment(experiment: ExperimentCreate):
    """Create a new experiment."""
    # Validate inputs
    if not dbmanager.validate_architecture_exists(experiment.architecture_name):
        raise HTTPException(status_code=400, detail=f"Architecture '{experiment.architecture_name}' not found")
    
    if not dbmanager.validate_dataset_exists(experiment.dataset_name):
        raise HTTPException(status_code=400, detail=f"Dataset '{experiment.dataset_name}' not found")
    
    if experiment.num_clients < 1:
        raise HTTPException(status_code=400, detail="Number of clients must be at least 1")
    
    if not experiment.parameters:
        raise HTTPException(status_code=400, detail="Parameters are required")
    
    conn = dbmanager.connection
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO experiments
            (name, description, dataset_name, architecture_name, num_clients, iid, status, parameters)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                experiment.name,
                experiment.description,
                experiment.dataset_name,
                experiment.architecture_name,
                experiment.num_clients,
                experiment.iid,
                "pending",
                json.dumps(experiment.parameters),
            ),
        )

        experiment_id = cursor.lastrowid
        conn.commit()

        # Return the created experiment
        cursor.execute("SELECT * FROM experiments WHERE id = ?", (experiment_id,))
        created_experiment = dict(cursor.fetchone())

        return created_experiment

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()


@router.get("/{experiment_id}", response_model=Dict)
def get_experiment(experiment_id: int):
    """Get a specific experiment."""
    conn = dbmanager.connection
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM experiments WHERE id = ?", (experiment_id,))
    experiment = cursor.fetchone()
    conn.close()

    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    return dict(experiment)


@router.put("/{experiment_id}", response_model=Dict)
def update_experiment(experiment_id: int, update_data: ExperimentUpdate):
    """Update an experiment."""
    conn = dbmanager.connection
    cursor = conn.cursor()

    # Get current experiment
    cursor.execute("SELECT * FROM experiments WHERE id = ?", (experiment_id,))
    experiment = cursor.fetchone()

    if not experiment:
        conn.close()
        raise HTTPException(status_code=404, detail="Experiment not found")

    try:
        # Build update query
        updates = []
        params = []

        if update_data.name is not None:
            updates.append("name = ?")
            params.append(update_data.name)

        if update_data.description is not None:
            updates.append("description = ?")
            params.append(update_data.description)

        if update_data.status is not None:
            updates.append("status = ?")
            params.append(update_data.status)

        if update_data.parameters is not None:
            updates.append("parameters = ?")
            params.append(json.dumps(update_data.parameters))

        updates.append("updated_at = ?")
        params.append(datetime.now().isoformat())

        params.append(experiment_id)

        query = f"UPDATE experiments SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        conn.commit()

        # Return updated experiment
        cursor.execute("SELECT * FROM experiments WHERE id = ?", (experiment_id,))
        updated_experiment = dict(cursor.fetchone())

        return updated_experiment

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()


@router.get("/{experiment_id}/results", response_model=List[Dict])
def get_experiment_results(experiment_id: int):
    """Get results for a specific experiment."""
    conn = dbmanager.connection
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM experiment_results
        WHERE experiment_id = ?
        ORDER BY round, timestamp
    """,
        (experiment_id,),
    )

    results = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return results


@router.post("/{experiment_id}/results", response_model=Dict)
def add_experiment_result(experiment_id: int, result: Dict):
    """Add a result for an experiment."""
    conn = dbmanager.connection
    cursor = conn.cursor()

    # Verify experiment exists
    cursor.execute("SELECT id FROM experiments WHERE id = ?", (experiment_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Experiment not found")

    try:
        cursor.execute(
            """
            INSERT INTO experiment_results
            (experiment_id, client_id, round, accuracy, loss, metrics)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                experiment_id,
                result.get("client_id"),
                result.get("round"),
                result.get("accuracy"),
                result.get("loss"),
                json.dumps(result.get("metrics", {})),
            ),
        )

        result_id = cursor.lastrowid
        conn.commit()

        # Return the created result
        cursor.execute("SELECT * FROM experiment_results WHERE id = ?", (result_id,))
        created_result = dict(cursor.fetchone())

        return created_result

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()


@router.post("/{experiment_id}/run", response_model=Dict)
def run_experiment(experiment_id: int):
    """Run an experiment using ARCH-FL core."""
    # Validate experiment exists
    if not dbmanager.validate_experiment_exists(experiment_id):
        raise HTTPException(status_code=404, detail="Experiment not found")
    
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
        raise HTTPException(status_code=400, detail="Experiment is already running")
    
    # Validate architecture and dataset still exist
    if not dbmanager.validate_architecture_exists(experiment_dict["architecture_name"]):
        raise HTTPException(status_code=400, detail=f"Architecture '{experiment_dict['architecture_name']}' not found")
    
    if not dbmanager.validate_dataset_exists(experiment_dict["dataset_name"]):
        raise HTTPException(status_code=400, detail=f"Dataset '{experiment_dict['dataset_name']}' not found")

    # Update status to running
    conn = dbmanager.connection
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE experiments SET status = ?, updated_at = ? WHERE id = ?",
        ("running", datetime.now().isoformat(), experiment_id),
    )
    conn.commit()
    conn.close()

    # Start experiment execution in background
    import threading

    def execute_experiment():
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
                    experiment_dict["architecture_name"]
                )

                # Get dataset
                dataset_info = data_registry.get_dataset_info(
                    experiment_dict["dataset_name"]
                )

                # Create model
                model = arch_registry.create_model(
                    experiment_dict["architecture_name"],
                    input_size=dataset_info.get("input_size", 28),
                )

                # Create coordinator with callback
                coordinator = Coordinator(
                    model,
                    aggregation_method=experiment_dict["parameters"].get(
                        "aggregation_method", "fed_avg"
                    ),
                    progress_callback=progress_callback,
                )

                # Get training parameters
                params = json.loads(experiment_dict["parameters"])
                num_rounds = params.get("num_rounds", 5)
                num_clients = experiment_dict["num_clients"]

                # Run federated training
                federated_average(
                    coordinator=coordinator,
                    dataset_name=experiment_dict["dataset_name"],
                    num_clients=num_clients,
                    num_rounds=num_rounds,
                    iid=experiment_dict["iid"],
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

    # Start execution thread
    thread = threading.Thread(target=execute_experiment, daemon=True)
    thread.start()

    return {
        "status": "started",
        "message": "Experiment execution started",
        "experiment_id": experiment_id,
    }


@router.post("/{experiment_id}/cancel", response_model=Dict)
def cancel_experiment(experiment_id: int):
    """Cancel a running experiment."""
    # Get experiment details
    conn = dbmanager.connection
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM experiments WHERE id = ?", (experiment_id,))
    experiment = cursor.fetchone()
    conn.close()

    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    experiment_dict = dict(experiment)

    # Only allow cancellation of running experiments
    if experiment_dict["status"] not in ["running", "pending"]:
        raise HTTPException(
            status_code=400,
            detail="Only running or pending experiments can be cancelled",
        )

    # Update status to cancelled
    conn = dbmanager.connection
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE experiments SET status = ?, updated_at = ? WHERE id = ?",
        ("cancelled", datetime.now().isoformat(), experiment_id),
    )
    conn.commit()
    conn.close()

    return {
        "status": "cancelled",
        "message": "Experiment cancelled successfully",
        "experiment_id": experiment_id,
    }


@router.post("/{experiment_id}/delete", response_model=Dict)
def delete_experiment(experiment_id: int):
    """Delete an experiment."""
    # Get experiment details
    conn = dbmanager.connection
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM experiments WHERE id = ?", (experiment_id,))
    experiment = cursor.fetchone()
    conn.close()

    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    experiment_dict = dict(experiment)

    # Cannot delete running experiments
    if experiment_dict["status"] == "running":
        raise HTTPException(
            status_code=400,
            detail="Cannot delete a running experiment. Please cancel it first.",
        )

    # Delete experiment results first
    conn = dbmanager.connection
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM experiment_results WHERE experiment_id = ?", (experiment_id,)
    )

    # Delete the experiment
    cursor.execute("DELETE FROM experiments WHERE id = ?", (experiment_id,))
    conn.commit()
    conn.close()

    return {
        "status": "deleted",
        "message": "Experiment deleted successfully",
        "experiment_id": experiment_id,
    }


@router.post("/{experiment_id}/restart", response_model=Dict)
def restart_experiment(experiment_id: int):
    """Restart a completed or cancelled experiment."""
    # Get experiment details
    conn = dbmanager.connection
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM experiments WHERE id = ?", (experiment_id,))
    experiment = cursor.fetchone()
    conn.close()

    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    experiment_dict = dict(experiment)

    # Only allow restart of completed or cancelled experiments
    if experiment_dict["status"] not in ["completed", "cancelled", "failed"]:
        raise HTTPException(
            status_code=400,
            detail="Only completed, cancelled, or failed experiments can be restarted",
        )

    # Update status to pending (will be set to running when execution starts)
    conn = dbmanager.connection
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE experiments SET status = ?, updated_at = ? WHERE id = ?",
        ("pending", datetime.now().isoformat(), experiment_id),
    )
    conn.commit()
    conn.close()

    # Start experiment execution in background
    import threading

    def execute_experiment():
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
                    experiment_dict["architecture_name"]
                )

                # Get dataset
                dataset_info = data_registry.get_dataset_info(
                    experiment_dict["dataset_name"]
                )

                # Create model
                model = arch_registry.create_model(
                    experiment_dict["architecture_name"],
                    input_size=dataset_info.get("input_size", 28),
                )

                # Create coordinator with callback
                coordinator = Coordinator(
                    model,
                    aggregation_method=experiment_dict["parameters"].get(
                        "aggregation_method", "fed_avg"
                    ),
                    progress_callback=progress_callback,
                )

                # Get training parameters
                params = json.loads(experiment_dict["parameters"])
                num_rounds = params.get("num_rounds", 5)
                num_clients = experiment_dict["num_clients"]

                # Run federated training
                federated_average(
                    coordinator=coordinator,
                    dataset_name=experiment_dict["dataset_name"],
                    num_clients=num_clients,
                    num_rounds=num_rounds,
                    iid=experiment_dict["iid"],
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

    # Start execution thread
    thread = threading.Thread(target=execute_experiment, daemon=True)
    thread.start()

    return {
        "status": "restarted",
        "message": "Experiment restarted successfully",
        "experiment_id": experiment_id,
    }


@router.post("/actions", response_model=Dict)
def batch_experiment_actions(action_data: Dict):
    """Perform batch actions on multiple experiments."""
    action_type = action_data.get("action")
    experiment_ids = action_data.get("experiment_ids", [])

    if not action_type:
        raise HTTPException(status_code=400, detail="Action type is required")

    if not experiment_ids:
        raise HTTPException(status_code=400, detail="No experiments selected")

    results = []
    errors = []

    for experiment_id in experiment_ids:
        try:
            if action_type == "delete":
                result = delete_experiment(experiment_id)
            elif action_type == "cancel":
                result = cancel_experiment(experiment_id)
            elif action_type == "run":
                result = run_experiment(experiment_id)
            elif action_type == "restart":
                result = restart_experiment(experiment_id)
            else:
                raise HTTPException(
                    status_code=400, detail=f"Unknown action: {action_type}"
                )

            results.append(
                {
                    "experiment_id": experiment_id,
                    "status": "success",
                    "message": result.get("message"),
                }
            )
        except HTTPException as e:
            errors.append(
                {"experiment_id": experiment_id, "status": "error", "message": e.detail}
            )
        except Exception as e:
            errors.append(
                {"experiment_id": experiment_id, "status": "error", "message": str(e)}
            )

    return {
        "action": action_type,
        "total_experiments": len(experiment_ids),
        "successful": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors,
    }
