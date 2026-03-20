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

import torch
import math
from typing import Dict, Optional, Tuple, Any
from opacus import PrivacyEngine
from opacus.validators import ModuleValidator
from ..utils.logger import get_logger
from .noise_mechanisms import NoiseMechanism, GaussianNoise, LaplaceNoise

logger = get_logger(__name__)


class DPEngine:
    """
    Differential Privacy Engine for Federated Learning

    Handles privacy budget accounting, noise addition, and gradient clipping
    for both centralized (Opacus) and federated (local DP) scenarios.
    """

    def __init__(
        self,
        epsilon: float,
        delta: float,
        max_grad_norm: float = 1.0,
        noise_mechanism: str = "gaussian",
        noise_scale: Optional[float] = None,
        sensitivity: Optional[float] = None,
        target_epsilon: Optional[float] = None,
        target_delta: Optional[float] = None,
        batch_size: Optional[int] = None,
        dataset_size: Optional[int] = None,
        use_opacus: bool = True,  # Use Opacus for centralized DP, else local DP
    ):
        """
        Initialize DP Engine

        Args:
            epsilon: Privacy budget (ε)
            delta: Privacy failure probability (δ)
            max_grad_norm: Maximum gradient norm for clipping (C)
            noise_mechanism: Type of noise ("gaussian" or "laplace")
            noise_scale: Pre-calculated noise scale (if None, will be computed)
            sensitivity: Pre-calculated sensitivity (if None, will be computed)
            target_epsilon: Target epsilon for noise calibration
            target_delta: Target delta for noise calibration
            batch_size: Batch size for sensitivity calculation
            dataset_size: Dataset size for sensitivity calculation
            use_opacus: Whether to use Opacus for centralized DP
        """
        self.epsilon = epsilon
        self.delta = delta
        self.max_grad_norm = max_grad_norm
        self.noise_mechanism = noise_mechanism.lower()
        self.use_opacus = use_opacus

        # Store for sensitivity calculation
        self.batch_size = batch_size
        self.dataset_size = dataset_size

        # Initialize noise mechanism
        self._init_noise_mechanism(
            noise_scale, sensitivity, target_epsilon, target_delta
        )

        # Initialize privacy engine (Opacus)
        self.privacy_engine = None
        if use_opacus:
            self.privacy_engine = PrivacyEngine()

        # Track privacy spent
        self.total_privacy_spent = {"epsilon": 0.0, "delta": delta}
        self.rounds_completed = 0

    def _init_noise_mechanism(
        self,
        noise_scale: Optional[float],
        sensitivity: Optional[float],
        target_epsilon: Optional[float],
        target_delta: Optional[float],
    ) -> None:
        """Initialize noise mechanism with calculated parameters"""

        # Calculate sensitivity if not provided
        if sensitivity is None:
            if self.batch_size and self.dataset_size:
                self.sensitivity = self._compute_sensitivity()
            else:
                self.sensitivity = self.max_grad_norm  # Default to max_grad_norm
                logger.warning("Using max_grad_norm as sensitivity - may be inaccurate")
        else:
            self.sensitivity = sensitivity

        # Calculate noise scale if not provided
        if noise_scale is None:
            if target_epsilon and target_delta:
                self.noise_scale = self._calibrate_noise(
                    target_epsilon, target_delta, self.sensitivity
                )
            else:
                self.noise_scale = self._get_default_noise_scale()
                logger.warning(f"Using default noise scale: {self.noise_scale}")
        else:
            self.noise_scale = noise_scale

        # Create noise mechanism instance
        if self.noise_mechanism == "gaussian":
            self.noise = GaussianNoise(noise_scale=self.noise_scale)
        elif self.noise_mechanism == "laplace":
            self.noise = LaplaceNoise(
                sensitivity=self.sensitivity, epsilon=self.epsilon
            )
        else:
            raise ValueError(f"Unknown noise mechanism: {self.noise_mechanism}")

        logger.info(
            f"DP Engine initialized: ε={self.epsilon}, δ={self.delta}, "
            f"C={self.max_grad_norm}, σ={self.noise_scale}, "
            f"Δ={self.sensitivity}, mechanism={self.noise_mechanism}"
        )

    def _compute_sensitivity(self) -> float:
        """Compute sensitivity for differential privacy"""
        if not self.batch_size or not self.dataset_size:
            return self.max_grad_norm

        # Sampling probability = batch_size / dataset_size
        # For federated learning, sensitivity = 2 * C * sampling_prob
        sampling_prob = self.batch_size / self.dataset_size
        return 2 * self.max_grad_norm * sampling_prob

    def _calibrate_noise(
        self, epsilon: float, delta: float, sensitivity: float
    ) -> float:
        """Calibrate Gaussian noise scale for (ε,δ)-DP"""
        if epsilon <= 0 or delta <= 0:
            return 0.0

        # Standard Gaussian noise calibration for (ε,δ)-DP
        # σ = Δ * √(2 * ln(1.25/δ)) / ε
        return sensitivity * math.sqrt(2 * math.log(1.25 / delta)) / epsilon

    def _get_default_noise_scale(self) -> float:
        """Get default noise scale based on epsilon"""
        if self.epsilon == float("inf"):
            return 0.0
        # Default: σ = 1/ε (simplified)
        return 1.0 / self.epsilon if self.epsilon > 0 else 1.0

    def make_private(
        self,
        model: torch.nn.Module,
        optimizer: torch.optim.Optimizer,
        data_loader: torch.utils.data.DataLoader,
        epoch: Optional[int] = None,
    ) -> Tuple[torch.nn.Module, torch.optim.Optimizer, torch.utils.data.DataLoader]:
        """
        Apply DP to model training using Opacus (centralized DP)

        Returns:
            Tuple of (model, optimizer, data_loader) wrapped for DP
        """
        if not self.use_opacus:
            logger.warning("Opacus not enabled - using local DP instead")
            return model, optimizer, data_loader

        # Validate model for DP compatibility
        if not ModuleValidator.is_valid(model):
            logger.warning("Model not DP-compatible, attempting fixes...")
            model = ModuleValidator.fix(model)

        try:
            # Calculate noise multiplier
            noise_multiplier = self.noise_scale / self.max_grad_norm

            model, optimizer, data_loader = self.privacy_engine.make_private(
                module=model,
                optimizer=optimizer,
                data_loader=data_loader,
                noise_multiplier=noise_multiplier,
                max_grad_norm=self.max_grad_norm,
            )

            logger.info(f"Applied DP to model: noise_multiplier={noise_multiplier:.4f}")
            return model, optimizer, data_loader

        except Exception as e:
            logger.error(f"Failed to apply DP: {e}")
            raise

    def add_noise_to_updates(
        self, updates: Dict[str, torch.Tensor], is_gradient: bool = False
    ) -> Dict[str, torch.Tensor]:
        """
        Add noise to model updates (for local DP)

        Args:
            updates: Dictionary of model parameters or gradients
            is_gradient: If True, treat updates as gradients and clip first

        Returns:
            Noisy updates dictionary
        """
        if self.noise_scale == 0:
            return updates

        # Clip gradients if needed
        if is_gradient:
            updates = self._clip_updates(updates)

        # Add noise
        noisy_updates = self.noise.add_noise(updates)

        # Track privacy budget (simplified composition)
        self._track_privacy_spent()

        return noisy_updates

    def _clip_updates(
        self, updates: Dict[str, torch.Tensor]
    ) -> Dict[str, torch.Tensor]:
        """Clip updates to max_grad_norm"""
        # Compute total norm
        total_norm_sq = sum(torch.sum(update**2).item() for update in updates.values())
        total_norm = math.sqrt(total_norm_sq)

        # Apply clipping
        if total_norm > self.max_grad_norm:
            clip_coef = self.max_grad_norm / (total_norm + 1e-6)
            clipped_updates = {}
            for key, update in updates.items():
                clipped_updates[key] = update * clip_coef
            return clipped_updates

        return updates

    def _track_privacy_spent(self) -> None:
        """Track privacy budget consumption (simplified composition)"""
        self.rounds_completed += 1
        # Simple composition (advanced composition would be better)
        self.total_privacy_spent["epsilon"] += (
            self.epsilon / 10
        )  # Conservative estimate

        if self.total_privacy_spent["epsilon"] > self.epsilon:
            logger.warning(
                f"Privacy budget exceeded: {self.total_privacy_spent['epsilon']:.4f} > {self.epsilon}"
            )

    def get_privacy_spent(self) -> Dict[str, float]:
        """Get current privacy budget consumption"""
        if self.use_opacus and self.privacy_engine:
            try:
                epsilon = self.privacy_engine.get_epsilon(delta=self.delta)
                return {"epsilon": epsilon, "delta": self.delta}
            except Exception as e:
                logger.error(f"Failed to get privacy spent: {e}")
                return self.total_privacy_spent
        else:
            return self.total_privacy_spent

    def reset_privacy_budget(self) -> None:
        """Reset privacy budget tracking"""
        self.rounds_completed = 0
        self.total_privacy_spent = {"epsilon": 0.0, "delta": self.delta}
        logger.info("Privacy budget reset")
