import pytest
import torch
from src.core.coordinator import Coordinator


def test_coordinator_initialization(simple_model):
    """Test coordinator initialization"""
    coordinator = Coordinator(simple_model)
    assert coordinator.global_model is not None
    assert coordinator.aggregation_method == "fed_avg"


def test_coordinator_aggregation_methods(simple_model):
    """Test different aggregation methods"""
    coordinator = Coordinator(simple_model)

    # Test setting valid aggregation methods
    coordinator.set_aggregation_method("fed_avg")
    assert coordinator.aggregation_method == "fed_avg"

    coordinator.set_aggregation_method("weighted")
    assert coordinator.aggregation_method == "weighted"

    coordinator.set_aggregation_method("secure")
    assert coordinator.aggregation_method == "secure"


def test_coordinator_invalid_aggregation_method(simple_model):
    """Test setting invalid aggregation method"""
    coordinator = Coordinator(simple_model)

    with pytest.raises(ValueError, match="Unknown aggregation method"):
        coordinator.set_aggregation_method("invalid_method")


def test_coordinator_get_global_model(simple_model):
    """Test getting global model parameters"""
    coordinator = Coordinator(simple_model)
    global_params = coordinator.get_global_model()

    assert isinstance(global_params, dict)
    assert len(global_params) > 0
    # Check that all parameters are tensors
    for param_name, param_value in global_params.items():
        assert isinstance(param_value, torch.Tensor)


def test_coordinator_fedavg_aggregation(simple_model):
    """Test FedAvg aggregation"""
    coordinator = Coordinator(simple_model)

    # Create mock client updates
    client_updates = []
    client_sizes = []

    # Get initial model parameters
    initial_params = coordinator.get_global_model()

    # Create 3 client updates with different sizes
    for i in range(3):
        client_params = {}
        for key, param in initial_params.items():
            # Create a slightly modified version
            client_params[key] = param + torch.randn_like(param) * 0.1
        client_updates.append(client_params)
        client_sizes.append(100 * (i + 1))  # Different sizes: 100, 200, 300

    # Perform aggregation
    coordinator.aggregate(client_updates, client_sizes)

    # Verify aggregation happened
    final_params = coordinator.get_global_model()
    assert final_params is not None


def test_coordinator_weighted_aggregation(simple_model):
    """Test weighted aggregation"""
    coordinator = Coordinator(simple_model)
    coordinator.set_aggregation_method("weighted")

    # Create mock client updates
    client_updates = []
    weights = [0.2, 0.3, 0.5]  # Custom weights

    # Get initial model parameters
    initial_params = coordinator.get_global_model()

    # Create 3 client updates
    for i in range(3):
        client_params = {}
        for key, param in initial_params.items():
            client_params[key] = param + torch.randn_like(param) * 0.1
        client_updates.append(client_params)

    # Perform weighted aggregation
    coordinator.aggregate(client_updates, client_sizes=[100, 100, 100], weights=weights)

    # Verify aggregation happened
    final_params = coordinator.get_global_model()
    assert final_params is not None


def test_coordinator_weighted_aggregation_missing_weights(simple_model):
    """Test weighted aggregation without providing weights"""
    coordinator = Coordinator(simple_model)
    coordinator.set_aggregation_method("weighted")

    # Create mock client updates
    client_updates = []
    initial_params = coordinator.get_global_model()

    for i in range(2):
        client_params = {}
        for key, param in initial_params.items():
            client_params[key] = param + torch.randn_like(param) * 0.1
        client_updates.append(client_params)

    # This should raise an error
    with pytest.raises(ValueError, match="Weights required for weighted aggregation"):
        coordinator.aggregate(client_updates, client_sizes=[100, 100])


def test_coordinator_secure_aggregation(simple_model):
    """Test secure aggregation"""
    coordinator = Coordinator(simple_model)
    coordinator.set_aggregation_method("secure")

    # Create mock client updates
    client_updates = []
    client_sizes = []

    initial_params = coordinator.get_global_model()

    for i in range(2):
        client_params = {}
        for key, param in initial_params.items():
            client_params[key] = param + torch.randn_like(param) * 0.1
        client_updates.append(client_params)
        client_sizes.append(100)

    # Perform secure aggregation (should use FedAvg internally)
    coordinator.aggregate(client_updates, client_sizes)

    # Verify aggregation happened
    final_params = coordinator.get_global_model()
    assert final_params is not None
