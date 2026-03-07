"""
Tests for dashboard integration with ARCH-FL core.
"""

import pytest
import tempfile
import os
import json
from src.core.dashboard_integration import DashboardConnector, create_dashboard_callback
from src.core.coordinator import Coordinator
import torch
import torch.nn as nn


class SimpleModel(nn.Module):
    """Simple model for testing."""
    def __init__(self):
        super().__init__()
        self.fc = nn.Linear(10, 2)
    
    def forward(self, x):
        return self.fc(x)


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    # Create tables
    conn = DashboardConnector(db_path).get_db_connection()
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
    
    yield db_path
    
    # Cleanup
    os.unlink(db_path)


def test_dashboard_connector_initialization(temp_db):
    """Test DashboardConnector initialization."""
    connector = DashboardConnector(temp_db)
    assert connector.db_path == temp_db
    assert os.path.exists(temp_db)


def test_create_experiment_record(temp_db):
    """Test creating an experiment record."""
    connector = DashboardConnector(temp_db)
    
    experiment_data = {
        "name": "Test Experiment",
        "description": "Testing dashboard integration",
        "dataset_name": "pneumoniamnist",
        "architecture_name": "simple_cnn",
        "num_clients": 5,
        "iid": True,
        "status": "pending",
        "parameters": {"num_rounds": 10, "learning_rate": 0.01}
    }
    
    experiment_id = connector.create_experiment_record(experiment_data)
    assert experiment_id > 0
    
    # Verify the record was created
    experiment = connector.get_experiment_by_id(experiment_id)
    assert experiment is not None
    assert experiment["name"] == "Test Experiment"
    assert experiment["dataset_name"] == "pneumoniamnist"
    assert experiment["num_clients"] == 5


def test_update_experiment_status(temp_db):
    """Test updating experiment status."""
    connector = DashboardConnector(temp_db)
    
    # Create an experiment first
    experiment_data = {
        "name": "Status Test",
        "dataset_name": "test",
        "architecture_name": "test",
        "num_clients": 1,
        "iid": True,
        "parameters": {}
    }
    
    experiment_id = connector.create_experiment_record(experiment_data)
    
    # Update status
    connector.update_experiment_status(experiment_id, "running")
    
    # Verify status was updated
    experiment = connector.get_experiment_by_id(experiment_id)
    assert experiment["status"] == "running"


def test_update_experiment_status_with_metrics(temp_db):
    """Test updating experiment status with metrics."""
    connector = DashboardConnector(temp_db)
    
    # Create an experiment
    experiment_data = {
        "name": "Metrics Test",
        "dataset_name": "test",
        "architecture_name": "test",
        "num_clients": 1,
        "iid": True,
        "parameters": {}
    }
    
    experiment_id = connector.create_experiment_record(experiment_data)
    
    # Update status with metrics
    metrics = {
        "round": 1,
        "accuracy": 0.85,
        "loss": 0.25,
        "additional_metrics": {"precision": 0.82, "recall": 0.80}
    }
    
    connector.update_experiment_status(experiment_id, "running", metrics)
    
    # Verify status was updated and result was added
    experiment = connector.get_experiment_by_id(experiment_id)
    assert experiment["status"] == "running"
    
    # Check that result was added
    conn = connector.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM experiment_results WHERE experiment_id = ?", (experiment_id,))
    result = cursor.fetchone()
    conn.close()
    
    assert result is not None
    assert result["round"] == 1
    assert result["accuracy"] == 0.85
    assert result["loss"] == 0.25


def test_add_experiment_result(temp_db):
    """Test adding experiment results."""
    connector = DashboardConnector(temp_db)
    
    # Create an experiment
    experiment_data = {
        "name": "Result Test",
        "dataset_name": "test",
        "architecture_name": "test",
        "num_clients": 1,
        "iid": True,
        "parameters": {}
    }
    
    experiment_id = connector.create_experiment_record(experiment_data)
    
    # Add a result
    result_data = {
        "client_id": 1,
        "round": 2,
        "accuracy": 0.90,
        "loss": 0.15,
        "metrics": {"precision": 0.88, "recall": 0.89}
    }
    
    result_id = connector.add_experiment_result(experiment_id, result_data)
    assert result_id > 0
    
    # Verify result was added
    conn = connector.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM experiment_results WHERE id = ?", (result_id,))
    result = cursor.fetchone()
    conn.close()
    
    assert result is not None
    assert result["experiment_id"] == experiment_id
    assert result["client_id"] == 1
    assert result["round"] == 2
    assert result["accuracy"] == 0.90
    assert result["loss"] == 0.15


def test_dashboard_callback(temp_db):
    """Test the dashboard callback function."""
    connector = DashboardConnector(temp_db)
    
    # Create an experiment
    experiment_data = {
        "name": "Callback Test",
        "dataset_name": "test",
        "architecture_name": "test",
        "num_clients": 1,
        "iid": True,
        "parameters": {}
    }
    
    experiment_id = connector.create_experiment_record(experiment_data)
    
    # Create callback
    callback = create_dashboard_callback(experiment_id, connector)
    
    # Call callback with aggregation complete event
    metrics = {"num_clients": 5, "aggregation_method": "fed_avg"}
    callback(1, metrics, "aggregation_complete")
    
    # Verify experiment status was updated
    experiment = connector.get_experiment_by_id(experiment_id)
    assert experiment["status"] == "running"
    
    # Check that result was added
    conn = connector.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM experiment_results WHERE experiment_id = ?", (experiment_id,))
    result = cursor.fetchone()
    conn.close()
    
    assert result is not None
    assert result["round"] == 1


def test_coordinator_with_dashboard_callback(temp_db):
    """Test Coordinator with dashboard callback."""
    connector = DashboardConnector(temp_db)
    
    # Create an experiment
    experiment_data = {
        "name": "Coordinator Test",
        "dataset_name": "test",
        "architecture_name": "test",
        "num_clients": 1,
        "iid": True,
        "parameters": {}
    }
    
    experiment_id = connector.create_experiment_record(experiment_data)
    
    # Create callback
    callback = create_dashboard_callback(experiment_id, connector)
    
    # Create coordinator with callback
    model = SimpleModel()
    coordinator = Coordinator(model, progress_callback=callback)
    
    # Create mock client updates
    initial_params = coordinator.get_global_model()
    client_updates = []
    client_sizes = []
    
    for i in range(3):
        client_params = {}
        for key, param in initial_params.items():
            client_params[key] = param + torch.randn_like(param) * 0.1
        client_updates.append(client_params)
        client_sizes.append(100)
    
    # Perform aggregation with round number
    coordinator.aggregate(client_updates, client_sizes, round_num=1)
    
    # Verify callback was triggered
    experiment = connector.get_experiment_by_id(experiment_id)
    assert experiment["status"] == "running"
    
    # Check that result was added
    conn = connector.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM experiment_results WHERE experiment_id = ?", (experiment_id,))
    result = cursor.fetchone()
    conn.close()
    
    assert result is not None
    assert result["round"] == 1
    assert result["metrics"] is not None
    result_metrics = json.loads(result["metrics"])
    assert result_metrics["num_clients"] == 3
    assert result_metrics["aggregation_method"] == "fed_avg"


def test_coordinator_model_summary():
    """Test Coordinator model summary method."""
    model = SimpleModel()
    coordinator = Coordinator(model)
    
    summary = coordinator.get_model_summary()
    
    assert "num_parameters" in summary
    assert "num_layers" in summary
    assert "aggregation_method" in summary
    assert "model_type" in summary
    
    # SimpleModel has 1 layer (the Linear layer)
    assert summary["num_layers"] == 1
    # SimpleModel has 22 parameters (10*2 + 2 bias terms)
    assert summary["num_parameters"] == 22
    assert summary["aggregation_method"] == "fed_avg"
    assert summary["model_type"] == "SimpleModel"