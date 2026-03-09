"""
Comprehensive scalability and resource usage tests for ARCH-FL.
Tests different client counts (1, 10, 100) and tracks resource usage.
"""

import pytest
import time
import torch
import psutil
import os
import json
import matplotlib

matplotlib.use("Agg")  # Use non-interactive backend
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, Path(__file__).resolve().parent.parent.as_posix())

from src.models.model_factory import ModelFactory
from src.core.coordinator import Coordinator
from src.data.partitioning import partition_iid, partition_non_iid
from src.core.client import Client
from src.data.datasets import MedicalDataset


results = []


class ResourceTracker:
    """Track resource usage during experiments."""

    def __init__(self):
        self.timestamps = []
        self.cpu_percentages = []
        self.memory_usage = []
        self.start_time = None
        self.end_time = None

    def start_tracking(self):
        """Start tracking resources."""
        self.start_time = time.time()
        self._record_resources()

    def stop_tracking(self):
        """Stop tracking resources."""
        self.end_time = time.time()

        self._record_resources()

    def _record_resources(self):
        """Record current resource usage."""
        process = psutil.Process(os.getpid())
        self.timestamps.append(time.time())
        self.cpu_percentages.append(psutil.cpu_percent(interval=0.1))
        self.memory_usage.append(process.memory_info().rss / (1024 * 1024))  # MB

    def get_duration(self) -> float:
        """Get experiment duration in seconds."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0

    def get_average_cpu(self) -> float:
        """Get average CPU usage."""
        if self.cpu_percentages:
            return sum(self.cpu_percentages) / len(self.cpu_percentages)
        return 0.0

    def get_max_memory(self) -> float:
        """Get maximum memory usage."""
        if self.memory_usage:
            return max(self.memory_usage)
        return 0.0

    def to_dict(self) -> Dict:
        """Convert resource data to dictionary."""
        return {
            "duration_seconds": self.get_duration(),
            "average_cpu_percent": self.get_average_cpu(),
            "max_memory_mb": self.get_max_memory(),
            "timestamps": self.timestamps,
            "cpu_percentages": self.cpu_percentages,
            "memory_usage_mb": self.memory_usage,
        }


@pytest.fixture
def experiment_results_dir(tmp_path):
    """Create directory for experiment results."""
    results_dir = tmp_path / "experiment_results"
    results_dir.mkdir(exist_ok=True)
    return results_dir


def test_resource_usage_tracking():
    """Test that resource tracking works correctly."""
    tracker = ResourceTracker()

    # Start tracking
    tracker.start_tracking()

    # Simulate some work
    time.sleep(0.5)

    # Stop tracking
    tracker.stop_tracking()

    # Verify results
    assert tracker.get_duration() > 0.4  # Should be at least 0.4 seconds
    assert tracker.get_duration() < 1.0  # Should be less than 1 second
    assert tracker.get_average_cpu() >= 0
    assert tracker.get_max_memory() > 0

    # Verify dictionary conversion
    data = tracker.to_dict()
    assert "duration_seconds" in data
    assert "average_cpu_percent" in data
    assert "max_memory_mb" in data
    assert "timestamps" in data
    assert "cpu_percentages" in data
    assert "memory_usage_mb" in data


def test_dashboard_integration_with_resources(experiment_results_dir, num_clients=1):
    """Test dashboard integration with resource tracking."""
    from src.core.dashboard_integration import (
        DashboardConnector,
        create_dashboard_callback,
    )

    tracker = ResourceTracker()
    tracker.start_tracking()

    # Create dashboard connector
    db_path = str(experiment_results_dir / "test.db")
    connector = DashboardConnector(db_path)

    # Create tables
    conn = connector.get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS experiments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            dataset_name TEXT NOT NULL,
            architecture_name TEXT NOT NULL,
            num_clients INTEGER NOT NULL,
            iid BOOLEAN NOT NULL,
            status TEXT DEFAULT 'pending',
            parameters JSON NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS experiment_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            experiment_id INTEGER NOT NULL,
            client_id INTEGER,
            round INTEGER NOT NULL,
            accuracy REAL,
            loss REAL,
            metrics JSON,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (experiment_id) REFERENCES experiments(id)
        )
    """)

    conn.commit()
    conn.close()

    # Create experiment record
    experiment_data = {
        "name": "Resource Test",
        "dataset_name": "test",
        "architecture_name": "test",
        "num_clients": num_clients,
        "iid": True,
        "parameters": {},
    }

    experiment_id = connector.create_experiment_record(experiment_data)

    # Create callback
    callback = create_dashboard_callback(experiment_id, connector)

    # Create simple model and coordinator
    model = torch.nn.Linear(10, 2)
    coordinator = Coordinator(model, progress_callback=callback)

    # Create mock client updates
    initial_params = coordinator.get_global_model()
    client_updates = []
    client_sizes = []

    for i in range(num_clients):
        client_params = {}
        for key, param in initial_params.items():
            client_params[key] = param + torch.randn_like(param) * 0.1
        client_updates.append(client_params)
        client_sizes.append(100)

    # Perform aggregation
    coordinator.aggregate(client_updates, client_sizes, round_num=1)

    # Stop tracking
    tracker.stop_tracking()

    # Verify callback was triggered
    experiment = connector.get_experiment_by_id(experiment_id)
    assert experiment["status"] == "running"

    # Verify resource tracking
    assert tracker.get_duration() > 0
    assert tracker.get_max_memory() > 0

    # Save results
    results.append(
        {
            "experiment_name": f"dashboard_integration_{num_clients}",
            "num_clients": num_clients,
            "resources": tracker.to_dict(),
        }
    )

    results_file = experiment_results_dir / "dashboard_integration_results.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)

    assert results_file.exists()


def test_constraint_based_architecture_generation():
    """Test architecture generation with constraints."""
    from src.models.architecture_generator import ArchitectureGenerator

    generator = ArchitectureGenerator()

    # Test with memory constraint
    constraints = {"max_memory_mb": 100}
    config = generator.generate_architecture(
        dataset_name="mimic_cxr", input_shape=(1, 224, 224), constraints=constraints
    )

    # Verify constraint is satisfied
    validation = config["validation"]
    assert validation["valid"] is True
    assert validation["estimated_memory_mb"] <= constraints["max_memory_mb"] * 1.2

    # Test with parameter constraint
    constraints = {"max_parameters": 300000}
    config = generator.generate_architecture(
        dataset_name="mimic_cxr", input_shape=(1, 224, 224), constraints=constraints
    )

    validation = config["validation"]
    assert validation["valid"] is True
    assert validation["estimated_parameters"] <= constraints["max_parameters"] * 1.2


def test_nas_with_constraints():
    """Test neural architecture search with constraints."""
    from src.models.architecture_generator import ArchitectureGenerator

    generator = ArchitectureGenerator()

    constraints = {"max_memory_mb": 200, "max_parameters": 500000}

    nas_results = generator.neural_architecture_search(
        dataset_name="mimic_cxr",
        input_shape=(1, 224, 224),
        task_type="binary_classification",
        num_trials=2,
        constraints=constraints,
    )

    # Verify NAS completed successfully
    assert len(nas_results["trials"]) == 2
    assert nas_results["best_architecture"] is not None
    assert nas_results["best_score"] > -float("inf")

    # Verify all trials are valid
    for trial in nas_results["trials"]:
        validation = trial["validation"]
        assert validation["valid"] is True


if __name__ == "__main__":
    # Run tests manually for debugging
    test_resource_usage_tracking()
    print("✅ Resource tracking test passed")

    client_count = [
        1,
        5,
        10,
        50,
        100,
        300,
        1_000,
        10_000,
        100_000,
        300_000,
        500_000,
        1_000_000,
    ]

    results_dir = Path(__file__).parent.parent.absolute() / "assets/experiment_results"
    from rich.progress import (
        Progress,
        SpinnerColumn,
        TextColumn,
        BarColumn,
        TaskProgressColumn,
        TimeRemainingColumn,
    )

    with Progress() as progress:
        task = progress.add_task(
            "Progress", completed=0, total=len(range(1, 500_000, 1_000))
        )
        for count in range(1, 500_000, 1_000):
            if count == 0:
                continue
            # print("Client count:", count)
            results_dir.mkdir(exist_ok=True)
            test_dashboard_integration_with_resources(results_dir, count)
            progress.update(task, advance=1)

        print("✅ Dashboard integration test passed")
    test_constraint_based_architecture_generation()
    print("✅ Constraint-based architecture generation test passed")

    test_nas_with_constraints()
    print("✅ NAS with constraints test passed")

    print("\n✅ All scalability and resource tests completed successfully!")
