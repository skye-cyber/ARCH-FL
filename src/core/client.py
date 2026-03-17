from typing import Dict
import torch
import torch.nn as nn
# from tqdm.auto import tqdm


class Client:
    def __init__(
        self,
        client_id: int,
        model: nn.Module,
        train_loader: torch.utils.data.DataLoader,
        device: str = "cpu",
        loss_function: str = "cross_entropy",
    ):
        self.client_id = client_id
        self.model = model
        self.train_loader = train_loader
        self.device = device
        self.loss_function = loss_function

    def local_train(
        self, global_params: Dict[str, torch.Tensor], local_epochs: int, lr: float
    ) -> Dict[str, torch.Tensor]:
        self.model.load_state_dict(global_params)
        self.model.train()

        optimizer = torch.optim.SGD(self.model.parameters(), lr=lr)
        criterion = nn.CrossEntropyLoss()

        for epoch in range(local_epochs):
            for data, target in self.train_loader:
                data = data.to(self.device)
                target = torch.tensor(target).to(self.device)
                optimizer.zero_grad()
                output = self.model(data)
                loss = criterion(output, target)
                loss.backward()
                optimizer.step()

        return self.model.state_dict()

    def get_dataset_size(self) -> int:
        return len(self.train_loader.dataset)

    def local_train_with_metrics(
        self, global_params: Dict[str, torch.Tensor], local_epochs, learning_rate
    ):
        """
        Perform local training and return both model update and metrics
        """
        # Set model to training mode
        self.model.train()
        self.model.load_state_dict(global_params)

        optimizer = torch.optim.SGD(self.model.parameters(), lr=learning_rate)
        criterion = self._get_loss_function()

        total_loss = 0
        correct = 0
        total = 0

        for epoch in range(local_epochs):
            for batch_idx, (data, target) in enumerate(self.train_loader):
                data, target = data.to(self.device), target.to(self.device)

                optimizer.zero_grad()
                output = self.model(data)
                loss = criterion(output, target)
                loss.backward()
                optimizer.step()

                total_loss += loss.item()

                # Calculate accuracy
                pred = output.argmax(dim=1, keepdim=True)
                correct += pred.eq(target.view_as(pred)).sum().item()
                total += target.size(0)

        avg_loss = total_loss / (local_epochs * len(self.train_loader))
        accuracy = 100.0 * correct / total

        metrics = {"accuracy": accuracy, "loss": avg_loss, "samples": total}

        return self.model.state_dict(), metrics

    def _get_loss_function(self):
        """Get loss function based on configuration"""
        if self.loss_function == "cross_entropy":
            return torch.nn.CrossEntropyLoss()
        elif self.loss_function == "mse":
            return torch.nn.MSELoss()
        else:
            return torch.nn.CrossEntropyLoss()  # Default
