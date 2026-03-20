import torch
import torch.nn as nn
from typing import Dict, Tuple, Optional
from ..privacy.dp_engine import DPEngine
from ..privacy.noise_mechanisms import clip_gradients
from ..utils.logger import logger


class LocalTrainer:
    def __init__(
        self,
        model: nn.Module,
        train_loader: torch.utils.data.DataLoader,
        device: str = "cpu",
        dp_config: Dict = None,
        dataset_size: Optional[int] = None,
    ):
        self.model = model
        self.train_loader = train_loader
        self.device = device
        self.dp_config = dp_config
        self.dataset_size = dataset_size or len(train_loader.dataset)
        self.dp_engine = None

        if dp_config and dp_config.get("enabled", False):
            # Initialize DP engine with proper parameters
            self.dp_engine = DPEngine(
                epsilon=dp_config.get("epsilon", 1.0),
                delta=dp_config.get("delta", 1e-5),
                max_grad_norm=dp_config.get("max_grad_norm", 1.0),
                noise_mechanism=dp_config.get("noise_mechanism", "gaussian"),
                batch_size=dp_config.get("batch_size", train_loader.batch_size),
                dataset_size=self.dataset_size,
                use_opacus=dp_config.get("use_opacus", False),
                target_epsilon=dp_config.get("epsilon", 1.0),
                target_delta=dp_config.get("delta", 1e-5),
            )

    def train_epoch(
        self, global_params: Dict[str, torch.Tensor], local_epochs: int, lr: float
    ) -> Tuple[Dict[str, torch.Tensor], Dict]:
        """
        Train for one epoch with DP
        """
        self.model.load_state_dict(global_params)
        self.model.train()

        optimizer = torch.optim.SGD(self.model.parameters(), lr=lr)
        criterion = nn.CrossEntropyLoss()

        # Apply DP if enabled
        if self.dp_engine:
            if self.dp_engine.use_opacus:
                # Centralized DP with Opacus
                self.model, optimizer, self.train_loader = self.dp_engine.make_private(
                    self.model, optimizer, self.train_loader
                )
            else:
                # Local DP - store for gradient clipping
                self._apply_dp = True

        total_loss = 0.0
        for epoch in range(local_epochs):
            for batch_idx, (data, target) in enumerate(self.train_loader):
                data, target = data.to(self.device), target.to(self.device)

                optimizer.zero_grad()
                output = self.model(data)
                loss = criterion(output, target)
                loss.backward()

                # Apply gradient clipping for local DP
                if self.dp_engine and not self.dp_engine.use_opacus:
                    clip_gradients(self.model, self.dp_engine.max_grad_norm)

                optimizer.step()
                total_loss += loss.item()

            avg_loss = total_loss / (len(self.train_loader) * local_epochs)
            logger.debug(f"Local epoch {epoch + 1}, Loss: {avg_loss:.4f}")

        # Get model updates
        updates = self.model.state_dict()

        # Add noise for local DP
        if self.dp_engine and not self.dp_engine.use_opacus:
            updates = self.dp_engine.add_noise_to_updates(updates)

        # Get privacy spent
        privacy_spent = None
        if self.dp_engine:
            privacy_spent = self.dp_engine.get_privacy_spent()
            logger.info(f"Privacy spent: {privacy_spent}")

        return updates, privacy_spent

    def compute_update(
        self, global_params: Dict[str, torch.Tensor], local_epochs: int, lr: float
    ) -> Tuple[Dict[str, torch.Tensor], Dict]:
        """
        Compute model update with DP
        """
        local_params, privacy_spent = self.train_epoch(global_params, local_epochs, lr)

        # Compute update as difference from global model
        update = {}
        for key in global_params.keys():
            if key in local_params:
                update[key] = local_params[key] - global_params[key]
            else:
                # Try to find matching parameter by shape
                for local_key, local_param in local_params.items():
                    if global_params[key].shape == local_param.shape:
                        update[key] = local_param - global_params[key]
                        break
                else:
                    # If no match found, use zeros
                    update[key] = torch.zeros_like(global_params[key])

        return update, privacy_spent

    def get_privacy_status(self) -> Dict:
        """
        Get current privacy budget status
        """
        if self.dp_engine:
            spent = self.dp_engine.get_privacy_spent()
            return {
                "epsilon_used": spent["epsilon"],
                "delta": spent["delta"],
                "epsilon_remaining": max(0, self.dp_engine.epsilon - spent["epsilon"]),
                "rounds": self.dp_engine.rounds_completed,
            }
        return {"enabled": False}
