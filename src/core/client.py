from typing import Dict, Optional
import torch
import torch.nn as nn
from ..privacy.dp_engine import DPEngine
from ..privacy.noise_mechanisms import clip_gradients


class Client:
    def __init__(
        self,
        client_id: int,
        model: nn.Module,
        train_loader: torch.utils.data.DataLoader,
        device: str = "cpu",
        loss_function: str = "cross_entropy",
        dp_engine: Optional[DPEngine] = None,  # Add DP engine parameter
    ):
        self.client_id = client_id
        self.model = model
        self.train_loader = train_loader
        self.device = device
        self.loss_function = loss_function
        self.dp_engine = dp_engine  # Store DP engine

        # Store dataset size for sensitivity calculation
        self.dataset_size = len(train_loader.dataset)

    def local_train(
        self, global_params: Dict[str, torch.Tensor], local_epochs: int, lr: float
    ) -> Dict[str, torch.Tensor]:
        self.model.load_state_dict(global_params)
        self.model.train()

        optimizer = torch.optim.SGD(self.model.parameters(), lr=lr)
        criterion = self._get_loss_function()

        # Apply centralized DP (Opacus) if enabled
        if self.dp_engine and self.dp_engine.use_opacus:
            self.model, optimizer, self.train_loader = self.dp_engine.make_private(
                self.model, optimizer, self.train_loader
            )

        for epoch in range(local_epochs):
            for data, target in self.train_loader:
                data = data.to(self.device)
                target = target.to(self.device)
                optimizer.zero_grad()
                output = self.model(data)
                loss = criterion(output, target)
                loss.backward()

                # Apply gradient clipping for local DP (non-Opacus)
                if self.dp_engine and not self.dp_engine.use_opacus:
                    clip_gradients(self.model, self.dp_engine.max_grad_norm)

                optimizer.step()

        # Get model updates
        updates = self.model.state_dict()

        # Add noise for local DP (non-Opacus)
        if self.dp_engine and not self.dp_engine.use_opacus:
            updates = self.dp_engine.add_noise_to_updates(updates)

        return updates

    def local_train_with_metrics(
        self, global_params: Dict[str, torch.Tensor], local_epochs, learning_rate
    ):
        """
        Perform local training and return both model update and metrics
        """
        self.model.train()
        self.model.load_state_dict(global_params)

        optimizer = torch.optim.SGD(self.model.parameters(), lr=learning_rate)
        criterion = self._get_loss_function()

        total_loss = 0
        correct = 0
        total = 0

        # Apply centralized DP if enabled
        if self.dp_engine and self.dp_engine.use_opacus:
            self.model, optimizer, self.train_loader = self.dp_engine.make_private(
                self.model, optimizer, self.train_loader
            )

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

                # Calculate accuracy
                pred = output.argmax(dim=1, keepdim=True)
                correct += pred.eq(target.view_as(pred)).sum().item()
                total += target.size(0)

        avg_loss = total_loss / (local_epochs * len(self.train_loader))
        accuracy = 100.0 * correct / total

        # Get updates
        updates = self.model.state_dict()

        # Add noise for local DP
        if self.dp_engine and not self.dp_engine.use_opacus:
            updates = self.dp_engine.add_noise_to_updates(updates)

        # Track privacy spending
        privacy_spent = None
        if self.dp_engine:
            privacy_spent = self.dp_engine.get_privacy_spent()

        metrics = {
            "accuracy": accuracy,
            "loss": avg_loss,
            "samples": total,
            "privacy_spent": privacy_spent,
        }

        return updates, metrics

    def _get_loss_function(self):
        """Get loss function based on configuration"""
        if self.loss_function == "cross_entropy":
            return torch.nn.CrossEntropyLoss()
        elif self.loss_function == "mse":
            return torch.nn.MSELoss()
        else:
            return torch.nn.CrossEntropyLoss()
