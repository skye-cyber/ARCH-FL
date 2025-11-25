import math
from typing import Tuple


def compute_sigma(target_epsilon: float, target_delta: float,
                  steps: int, sampling_rate: float) -> float:
    """Compute noise multiplier for (ε,δ)-DP using analytic Gaussian mechanism"""
    if target_epsilon == float('inf'):
        return 0.0

    # Simplified calculation - in practice use Opacus accounting
    return math.sqrt(2 * math.log(1.25 / target_delta)) / target_epsilon


def moments_accountant(steps: int, noise_multiplier: float,
                       sampling_rate: float, delta: float) -> float:
    """Compute epsilon using moments accountant (simplified)"""
    # Placeholder - Opacus handles this internally
    return noise_multiplier * sampling_rate * math.sqrt(steps)
