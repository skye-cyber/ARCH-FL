import torch
import math
from abc import ABC, abstractmethod
from typing import Dict, Optional


class NoiseMechanism(ABC):
    """Abstract base class for noise mechanisms"""

    @abstractmethod
    def add_noise(self, parameters: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
        """Add noise to parameters"""
        pass

    @abstractmethod
    def get_scale(self) -> float:
        """Get noise scale"""
        pass


class GaussianNoise(NoiseMechanism):
    """Gaussian noise mechanism for (ε,δ)-DP"""

    def __init__(
        self,
        noise_scale: float,
        sensitivity: Optional[float] = None,
        epsilon: Optional[float] = None,
        delta: Optional[float] = None,
    ):
        """
        Initialize Gaussian noise

        Args:
            noise_scale: Standard deviation of Gaussian noise (σ)
            sensitivity: Sensitivity (Δ) - used if calibrating
            epsilon: Privacy budget (ε) - used if calibrating
            delta: Privacy failure probability (δ) - used if calibrating
        """
        self.noise_scale = noise_scale

        # Store for potential recalibration
        self.sensitivity = sensitivity
        self.epsilon = epsilon
        self.delta = delta

    def add_noise(self, parameters: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
        """Add Gaussian noise to parameters"""
        noisy_parameters = {}

        for key, tensor in parameters.items():
            # Generate Gaussian noise
            noise = torch.randn_like(tensor) * self.noise_scale
            noisy_parameters[key] = tensor + noise

        return noisy_parameters

    def calibrate_noise(
        self, epsilon: float, delta: float, sensitivity: float
    ) -> float:
        """Calibrate noise scale for target (ε,δ)-DP"""
        if epsilon <= 0 or delta <= 0 or sensitivity <= 0:
            return 0.0

        # σ = Δ * √(2 * ln(1.25/δ)) / ε
        self.noise_scale = sensitivity * math.sqrt(2 * math.log(1.25 / delta)) / epsilon
        self.epsilon = epsilon
        self.delta = delta
        self.sensitivity = sensitivity

        return self.noise_scale

    def get_scale(self) -> float:
        """Get noise scale"""
        return self.noise_scale


class LaplaceNoise(NoiseMechanism):
    """Laplace noise mechanism for ε-DP"""

    def __init__(
        self, sensitivity: float, epsilon: float, scale: Optional[float] = None
    ):
        """
        Initialize Laplace noise

        Args:
            sensitivity: Sensitivity (Δ)
            epsilon: Privacy budget (ε)
            scale: Pre-calculated scale (if None, computed as sensitivity/epsilon)
        """
        self.sensitivity = sensitivity
        self.epsilon = epsilon
        self.scale = scale if scale is not None else sensitivity / epsilon

    def add_noise(self, parameters: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
        """Add Laplace noise to parameters"""
        noisy_parameters = {}

        for key, tensor in parameters.items():
            # Generate Laplace noise
            laplace = torch.distributions.Laplace(0, self.scale)
            noise = laplace.sample(tensor.shape)
            noisy_parameters[key] = tensor + noise

        return noisy_parameters

    def get_scale(self) -> float:
        """Get noise scale"""
        return self.scale


# Utility functions for backward compatibility
def add_gaussian_noise(
    parameters: Dict[str, torch.Tensor], noise_scale: float
) -> Dict[str, torch.Tensor]:
    """Add Gaussian noise to model parameters (legacy interface)"""
    noise = GaussianNoise(noise_scale)
    return noise.add_noise(parameters)


def add_laplace_noise(
    parameters: Dict[str, torch.Tensor], sensitivity: float, epsilon: float
) -> Dict[str, torch.Tensor]:
    """Add Laplace noise to model parameters (legacy interface)"""
    noise = LaplaceNoise(sensitivity, epsilon)
    return noise.add_noise(parameters)


def clip_gradients(model: torch.nn.Module, max_norm: float) -> None:
    """Clip gradients to a maximum L2 norm"""
    total_norm = 0.0
    for p in model.parameters():
        if p.grad is not None:
            param_norm = p.grad.data.norm(2)
            total_norm += param_norm.item() ** 2
    total_norm = total_norm**0.5

    clip_coef = max_norm / (total_norm + 1e-6)
    if clip_coef < 1:
        for p in model.parameters():
            if p.grad is not None:
                p.grad.data.mul_(clip_coef)


def compute_sensitivity(
    max_norm: float,
    dataset_size: int,
    batch_size: int,
    sampling_prob: Optional[float] = None,
) -> float:
    """Compute sensitivity for differential privacy"""
    if sampling_prob is None:
        sampling_prob = batch_size / dataset_size if dataset_size > 0 else 1.0
    return 2 * max_norm * sampling_prob


def calibrate_noise(
    epsilon: float, delta: float, sensitivity: float, mechanism: str = "gaussian"
) -> float:
    """Calibrate noise scale for (ε,δ)-DP"""
    if epsilon <= 0 or delta <= 0 or sensitivity <= 0:
        return 0.0

    if mechanism == "gaussian":
        # Gaussian noise for (ε,δ)-DP
        return sensitivity * math.sqrt(2 * math.log(1.25 / delta)) / epsilon
    elif mechanism == "laplace":
        # Laplace noise for ε-DP
        return sensitivity / epsilon
    else:
        raise ValueError(f"Unknown mechanism: {mechanism}")
