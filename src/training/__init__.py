"""Training module for ARCH-FL project"""
from .local_trainer import LocalTrainer
from .fedavg import FederatedTrainer

__all__ = ['LocalTrainer', 'FederatedTrainer']