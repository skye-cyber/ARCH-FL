from typing import Dict, Tuple
import torch
import torch.nn as nn


class Client:
    def __init__(
        self,
        client_id: int,
        model: nn.Module,
        train_loader: torch.utils.data.DataLoader,
        device: str = "cpu",
    ):
        self.client_id = client_id
        self.model = model
        self.train_loader = train_loader
        self.device = device

    def local_train(
        self, global_params: Dict[str, torch.Tensor], local_epochs: int, lr: float
    ) -> Dict[str, torch.Tensor]:
        self.model.load_state_dict(global_params)
        self.model.train()

        optimizer = torch.optim.SGD(self.model.parameters(), lr=lr)
        criterion = nn.CrossEntropyLoss()

        for epoch in range(local_epochs):
            for data, target in self.train_loader:
                data, target = data.to(self.device), target.to(self.device)
                optimizer.zero_grad()
                output = self.model(data)
                loss = criterion(output, target)
                loss.backward()
                optimizer.step()

        return self.model.state_dict()

    def get_dataset_size(self) -> int:
        return len(self.train_loader.dataset)


class Client_old:
    # DEPRECATED
    def __init__(
        self,
        client_id: int,
        model: nn.Module,
        train_loader: torch.utils.data.DataLoader,
        device: str = "cpu",
        dp_config: Dict = None,
    ):
        self.client_id = client_id
        self.model = model
        self.train_loader = train_loader
        self.device = device
        # Import LocalTrainer locally to avoid circular imports
        from ..training.local_trainer import LocalTrainer

        self.trainer = LocalTrainer(model, train_loader, device, dp_config)

    def local_train(
        self, global_params: Dict[str, torch.Tensor], local_epochs: int, lr: float
    ) -> Tuple[Dict[str, torch.Tensor], Dict]:

        update, privacy_spent = self.trainer.compute_update(
            global_params, local_epochs, lr
        )
        return update, privacy_spent

    def get_dataset_size(self) -> int:
        return len(self.train_loader.dataset)
