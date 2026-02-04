import torch
import torch.nn as nn
from src.privacy.dp_engine import DPEngine
# from src.models.architectures import SimpleCNN


def test_dp_engine_initialization(dp_config):
    """Test DP engine initialization"""
    dp_engine = DPEngine(
        epsilon=dp_config['epsilon'],
        delta=dp_config['delta'],
        max_grad_norm=dp_config['max_grad_norm']
    )

    assert dp_engine.epsilon == dp_config['epsilon']
    assert dp_engine.delta == dp_config['delta']
    assert dp_engine.max_grad_norm == dp_config['max_grad_norm']
    assert dp_engine.privacy_engine is not None


def test_dp_engine_noise_multiplier(dp_engine):
    """Test noise multiplier calculation"""
    # Test with finite epsilon
    noise_multiplier = dp_engine._get_noise_multiplier()
    expected = 1.0 / dp_engine.epsilon
    assert noise_multiplier == expected

    # Test with infinite epsilon (no DP)
    dp_engine.epsilon = float('inf')
    noise_multiplier = dp_engine._get_noise_multiplier()
    assert noise_multiplier == 0.0


def test_dp_engine_make_private(dp_engine, simple_model):
    """Test make_private method"""
    optimizer = torch.optim.SGD(simple_model.parameters(), lr=0.01)

    # Create a small dataset
    from torch.utils.data import DataLoader, TensorDataset
    data = torch.randn(10, 1, 28, 28)
    targets = torch.randint(0, 2, (10,))
    dataset = TensorDataset(data, targets)
    loader = DataLoader(dataset, batch_size=5)

    # Apply DP
    model, optimizer, loader = dp_engine.make_private(simple_model, optimizer, loader)

    # Verify DP is applied by checking model type and optimizer type
    from opacus.grad_sample import GradSampleModule
    from opacus.optimizers import DPOptimizer
    assert isinstance(model, GradSampleModule)
    assert isinstance(optimizer, DPOptimizer)


def test_dp_engine_disabled(dp_config):
    """Test DP engine with disabled DP"""
    dp_config['enabled'] = False
    dp_engine = DPEngine(
        epsilon=dp_config['epsilon'],
        delta=dp_config['delta'],
        max_grad_norm=dp_config['max_grad_norm']
    )

    # Should still initialize but won't apply DP
    assert dp_engine.epsilon == dp_config['epsilon']
    assert dp_engine.privacy_engine is not None


def test_dp_engine_privacy_spent(dp_engine, simple_model):
    """Test privacy spent tracking"""
    optimizer = torch.optim.SGD(simple_model.parameters(), lr=0.01)
    criterion = torch.nn.CrossEntropyLoss()

    # Create a small dataset
    from torch.utils.data import DataLoader, TensorDataset
    data = torch.randn(20, 1, 28, 28)
    targets = torch.randint(0, 2, (20,))
    dataset = TensorDataset(data, targets)
    loader = DataLoader(dataset, batch_size=5)

    # Apply DP
    model, optimizer, loader = dp_engine.make_private(simple_model, optimizer, loader)

    # Perform some training steps to accumulate privacy spending
    for batch_data, batch_targets in loader:
        optimizer.zero_grad()
        output = model(batch_data)
        loss = criterion(output, batch_targets)
        loss.backward()
        optimizer.step()
        break  # Just one step to accumulate some privacy spending

    # Get privacy spent
    privacy_spent = dp_engine.get_privacy_spent()

    # Should return a dictionary with privacy metrics
    assert isinstance(privacy_spent, dict)
    assert 'epsilon' in privacy_spent
    assert 'delta' in privacy_spent
    # Privacy spent should be greater than 0 after training
    assert privacy_spent['epsilon'] > 0


def test_dp_engine_different_epsilon_values():
    """Test DP engine with different epsilon values"""
    epsilon_values = [1.0, 2.0, 4.0, 8.0, float('inf')]

    for epsilon in epsilon_values:
        dp_engine = DPEngine(epsilon=epsilon, delta=1e-5, max_grad_norm=1.0)

        if epsilon != float('inf'):
            noise_multiplier = dp_engine._get_noise_multiplier()
            assert noise_multiplier > 0
        else:
            noise_multiplier = dp_engine._get_noise_multiplier()
            assert noise_multiplier == 0.0


def test_dp_engine_different_delta_values():
    """Test DP engine with different delta values"""
    delta_values = [1e-3, 1e-4, 1e-5, 1e-6]

    for delta in delta_values:
        dp_engine = DPEngine(epsilon=2.0, delta=delta, max_grad_norm=1.0)
        assert dp_engine.delta == delta


def test_dp_engine_different_max_grad_norm():
    """Test DP engine with different max grad norm values"""
    max_grad_norm_values = [0.5, 1.0, 2.0, 5.0]

    for max_grad_norm in max_grad_norm_values:
        dp_engine = DPEngine(epsilon=2.0, delta=1e-5, max_grad_norm=max_grad_norm)
        assert dp_engine.max_grad_norm == max_grad_norm


def test_dp_engine_integration_with_training(dp_engine, simple_model):
    """Test DP engine integration with a training step"""
    optimizer = torch.optim.SGD(simple_model.parameters(), lr=0.01)
    criterion = nn.CrossEntropyLoss()

    # Create a small dataset
    from torch.utils.data import DataLoader, TensorDataset
    data = torch.randn(20, 1, 28, 28)
    targets = torch.randint(0, 2, (20,))
    dataset = TensorDataset(data, targets)
    loader = DataLoader(dataset, batch_size=5)

    # Apply DP
    model, optimizer, loader = dp_engine.make_private(simple_model, optimizer, loader)

    # Perform one training step
    for batch_data, batch_targets in loader:
        optimizer.zero_grad()
        output = model(batch_data)
        loss = criterion(output, batch_targets)
        loss.backward()
        optimizer.step()
        break  # Just one step

    # Should complete without errors
    assert True
