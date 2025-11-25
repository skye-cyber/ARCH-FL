import torch
import math
from typing import Dict


def add_gaussian_noise(parameters: Dict[str, torch.Tensor],
                       noise_scale: float) -> Dict[str, torch.Tensor]:
    """Add Gaussian noise to model parameters"""
    noisy_parameters = {}
    for key, tensor in parameters.items():
        noise = torch.randn_like(tensor) * noise_scale
        noisy_parameters[key] = tensor + noise
    return noisy_parameters


def add_laplace_noise(parameters: Dict[str, torch.Tensor],
                      sensitivity: float, epsilon: float) -> Dict[str, torch.Tensor]:
    """Add Laplace noise to model parameters"""
    noisy_parameters = {}
    for key, tensor in parameters.items():
        scale = sensitivity / epsilon
        noise = torch.distributions.Laplace(0, scale).sample(tensor.shape)
        noisy_parameters[key] = tensor + noise
    return noisy_parameters


def clip_gradients(model: torch.nn.Module, max_norm: float) -> None:
    """Clip gradients to a maximum L2 norm"""
    total_norm = 0.0
    for p in model.parameters():
        if p.grad is not None:
            param_norm = p.grad.data.norm(2)
            total_norm += param_norm.item() ** 2
    total_norm = total_norm ** 0.5

    clip_coef = max_norm / (total_norm + 1e-6)
    if clip_coef < 1:
        for p in model.parameters():
            if p.grad is not None:
                p.grad.data.mul_(clip_coef)


def compute_sensitivity(max_norm: float, dataset_size: int, batch_size: int) -> float:
    """Compute sensitivity for differential privacy"""
    sampling_prob = batch_size / dataset_size
    return 2 * max_norm * sampling_prob


def calibrate_noise(epsilon: float, delta: float, sensitivity: float) -> float:
    """Calibrate Gaussian noise scale for (ε,δ)-DP"""
    if epsilon == 0 or delta == 0:
        return 0.0
    return sensitivity * math.sqrt(2 * math.log(1.25 / delta)) / epsilon
