import torch
from typing import List
from ..core.coordinator import Coordinator
from ..core.client import Client
from ..utils.logger import logger


class FederatedTrainer:
    def __init__(
        self,
        coordinator: Coordinator,
        clients: List[Client],
        test_loader: torch.utils.data.DataLoader,
        device: str = "cpu",
        loss_function: str = "cross_entropy",
    ):
        self.coordinator = coordinator
        self.clients = clients
        self.test_loader = test_loader
        self.device = device
        self.loss_function = loss_function

    def train_round(
        self, client_indices: List[int], local_epochs: int, lr: float
    ) -> float:
        client_updates = []
        client_sizes = []

        global_model = self.coordinator.get_global_model()

        for client_idx in client_indices:
            client = self.clients[client_idx]
            client_update = client.local_train(global_model, local_epochs, lr)
            client_updates.append(client_update)
            client_sizes.append(len(client.train_loader.dataset))

        self.coordinator.aggregate(client_updates, client_sizes)
        return self.evaluate()

    def evaluate(self) -> float:
        self.coordinator.global_model.eval()
        correct = 0
        total = 0

        with torch.no_grad():
            for data, target in self.test_loader:
                data, target = data.to(self.device), target.to(self.device)
                output = self.coordinator.global_model(data)
                pred = output.argmax(dim=1, keepdim=True)
                correct += pred.eq(target.view_as(pred)).sum().item()
                total += target.size(0)

        accuracy = 100.0 * correct / total
        logger.info(f"[*] Accuracy: {accuracy:.2f}%")
        return accuracy

    def evaluate_with_metrics(self) -> dict:
        """
        Evaluate the global model and return both accuracy and loss
        """
        self.coordinator.global_model.eval()
        criterion = self._get_loss_function()

        test_loss = 0
        correct = 0
        total = 0

        with torch.no_grad():
            for data, target in self.test_loader:
                data, target = data.to(self.device), target.to(self.device)
                output = self.coordinator.global_model(data)

                # Sum up batch loss
                test_loss += criterion(output, target).item()

                # Get the index of the max log-probability
                pred = output.argmax(dim=1, keepdim=True)
                correct += pred.eq(target.view_as(pred)).sum().item()
                total += target.size(0)

        test_loss /= len(self.test_loader)
        accuracy = 100.0 * correct / total

        return {
            "accuracy": accuracy,
            "loss": test_loss,
            "correct": correct,
            "total": total,
        }

    def _get_loss_function(self):
        """Get loss function based on configuration"""
        if self.loss_function == "cross_entropy":
            return torch.nn.CrossEntropyLoss()
        elif self.loss_function == "mse":
            return torch.nn.MSELoss()
        else:
            return torch.nn.CrossEntropyLoss()  # Default
