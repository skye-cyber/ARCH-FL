import torch
import torch.nn as nn
from typing import Dict, Tuple
from ..privacy.dp_engine import DPEngine
from ..utils.logger import get_logger

logger = get_logger(__name__)


class LocalTrainer:
    def __init__(self, model: nn.Module, train_loader: torch.utils.data.DataLoader,
                 device: str = "cpu", dp_config: Dict = None):
        self.model = model
        self.train_loader = train_loader
        self.device = device
        self.dp_config = dp_config
        self.dp_engine = None

        if dp_config and dp_config.get('enabled', False):
            self.dp_engine = DPEngine(
                epsilon=dp_config.get('epsilon', 1.0),
                delta=dp_config.get('delta', 1e-5),
                max_grad_norm=dp_config.get('max_grad_norm', 1.0)
            )

    def train_epoch(self, global_params: Dict[str, torch.Tensor],
                    local_epochs: int, lr: float) -> Dict[str, torch.Tensor]:

        self.model.load_state_dict(global_params)
        self.model.train()

        optimizer = torch.optim.SGD(self.model.parameters(), lr=lr)
        criterion = nn.CrossEntropyLoss()

        # Apply DP if enabled
        if self.dp_engine:
            self.model, optimizer, self.train_loader = self.dp_engine.make_private(
                self.model, optimizer, self.train_loader
            )

        for epoch in range(local_epochs):
            total_loss = 0.0
            for batch_idx, (data, target) in enumerate(self.train_loader):
                data, target = data.to(self.device), target.to(self.device)
                optimizer.zero_grad()
                output = self.model(data)
                loss = criterion(output, target)
                loss.backward()
                optimizer.step()
                total_loss += loss.item()

            avg_loss = total_loss / len(self.train_loader)
            logger.debug(f"Client local epoch {epoch + 1}, Loss: {avg_loss:.4f}")

        # Get privacy spent if DP enabled
        privacy_spent = None
        if self.dp_engine:
            privacy_spent = self.dp_engine.get_privacy_spent()
            logger.info(f"Privacy spent: {privacy_spent}")

        return self.model.state_dict(), privacy_spent

    def compute_update(self, global_params: Dict[str, torch.Tensor],
                       local_epochs: int, lr: float) -> Tuple[Dict[str, torch.Tensor], Dict]:

        local_params, privacy_spent = self.train_epoch(global_params, local_epochs, lr)

        # Compute update as difference from global model
        update = {}
        for key in global_params.keys():
            update[key] = local_params[key] - global_params[key]

        return update, privacy_spent
