import pytest
# import path_init
from src.models.architectures import SimpleCNN
from src.data.datasets import MedicalDataset
from src.core.coordinator import Coordinator
from src.core.client import Client
from src.training.local_trainer import LocalTrainer
from src.privacy.dp_engine import DPEngine
import numpy as np


@pytest.fixture
def simple_model():
    """Create a simple CNN model for testing"""
    return SimpleCNN(num_classes=2)


@pytest.fixture
def synthetic_dataset():
    """Create a small synthetic dataset for testing"""
    num_samples = 100
    data = np.random.randn(num_samples, 1, 28, 28).astype(np.float32)
    targets = np.random.randint(0, 2, num_samples)
    return MedicalDataset(data, targets)


@pytest.fixture
def coordinator(simple_model):
    """Create a coordinator instance"""
    return Coordinator(simple_model)


@pytest.fixture
def client(simple_model, synthetic_dataset):
    """Create a client instance"""
    from torch.utils.data import DataLoader
    loader = DataLoader(synthetic_dataset, batch_size=10, shuffle=False)
    return Client(client_id=1, model=simple_model, train_loader=loader)


@pytest.fixture
def dp_config():
    """DP configuration for testing"""
    return {
        'enabled': True,
        'epsilon': 2.0,
        'delta': 1e-5,
        'max_grad_norm': 1.0
    }


@pytest.fixture
def dp_engine(dp_config):
    """Create a DP engine instance"""
    return DPEngine(
        epsilon=dp_config['epsilon'],
        delta=dp_config['delta'],
        max_grad_norm=dp_config['max_grad_norm']
    )


@pytest.fixture
def local_trainer(simple_model, synthetic_dataset, dp_config):
    """Create a local trainer instance"""
    from torch.utils.data import DataLoader
    loader = DataLoader(synthetic_dataset, batch_size=10, shuffle=False)
    return LocalTrainer(simple_model, loader, dp_config=dp_config)
