import torch
from opacus import PrivacyEngine
from typing import Dict
from ..utils.logger import get_logger

logger = get_logger(__name__)


class DPEngine:
    """
    1. Privacy Budget (ε)
    Total allowable privacy loss over training; smaller ε means stronger privacy \
        but less model utility, as it accumulates across rounds.

    2. Noise Mechanism
    Method to add calibrated randomness (e.g., Gaussian or Laplace) to model
    updates, obscuring individual contributions while preserving aggregate utility.

    3. Noise Scale (σ)
    Standard deviation of added Gaussian noise; higher σ enhances privacy by\
        increasing randomness but reduces accuracy.

    4. Max-Grad-Norm (C)
    Clipper threshold for gradient norms; bounds update size to limit sensitivity\
        before noise addition, preventing outliers from dominating.

    5. Sensitivity (Δ)
    Maximum influence one data record can have on an output (e.g., L2 norm of\
        clipped gradients); determines required noise level for DP guarantees.
    """
    def __init__(self, epsilon: float, delta: float, max_grad_norm: float):
        self.epsilon = epsilon
        self.delta = delta
        self.max_grad_norm = max_grad_norm
        self.privacy_engine = PrivacyEngine()

    def make_private(self, model: torch.nn.Module,
                     optimizer: torch.optim.Optimizer,
                     data_loader: torch.utils.data.DataLoader) -> tuple:
        model, optimizer, data_loader = self.privacy_engine.make_private(
            module=model,
            optimizer=optimizer,
            data_loader=data_loader,
            noise_multiplier=self._get_noise_multiplier(),
            max_grad_norm=self.max_grad_norm,
        )
        logger.info(f"Applied DP with ε={self.epsilon}, δ={self.delta}")
        return model, optimizer, data_loader

    def _get_noise_multiplier(self) -> float:
        # Simplified - would calculate based on target epsilon
        return 1.0 / self.epsilon if self.epsilon != float('inf') else 0.0

    def get_privacy_spent(self) -> Dict[str, float]:
        epsilon = self.privacy_engine.get_epsilon(delta=self.delta)
        return {
            'epsilon': epsilon,
            'delta': self.delta
        }
