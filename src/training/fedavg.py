import torch
from typing import List, Optional
from ..core.coordinator import Coordinator
from ..core.client import Client
from ..privacy.dp_engine import DPEngine
from ..utils.logger import logger


class FederatedTrainer:
    def __init__(
        self,
        coordinator: Coordinator,
        clients: List[Client],
        test_loader: torch.utils.data.DataLoader,
        device: str = "cpu",
        loss_function: str = "cross_entropy",
        dp_engine: Optional[DPEngine] = None,  # Add DP engine
    ):
        self.coordinator = coordinator
        self.clients = clients
        self.test_loader = test_loader
        self.device = device
        self.loss_function = loss_function
        self.dp_engine = dp_engine  # Store for global DP application

        # Track privacy budget across rounds
        self.total_privacy_spent = {"epsilon": 0.0, "delta": 0.0}

    def train_round(
        self, client_indices: List[int], local_epochs: int, lr: float
    ) -> float:
        client_updates = []
        client_sizes = []

        global_model = self.coordinator.get_global_model()

        for client_idx in client_indices:
            client = self.clients[client_idx]
            # Pass DP engine to client if not already set
            if client.dp_engine is None and self.dp_engine:
                client.dp_engine = self.dp_engine

            client_update = client.local_train(global_model, local_epochs, lr)
            client_updates.append(client_update)
            client_sizes.append(client.dataset_size)

        # Aggregate updates
        self.coordinator.aggregate(client_updates, client_sizes)

        # Apply DP to aggregated model if using global DP
        if self.dp_engine and not self.dp_engine.use_opacus:
            self._apply_global_dp()

        return self.evaluate()

    def train_round_with_metrics(
        self, client_indices: List[int], local_epochs: int, lr: float
    ) -> dict:
        """
        Train round with detailed metrics including privacy tracking
        """
        client_updates = []
        client_sizes = []
        client_metrics = []

        global_model = self.coordinator.get_global_model()

        for client_idx in client_indices:
            client = self.clients[client_idx]

            # Pass DP engine to client if not already set
            if client.dp_engine is None and self.dp_engine:
                client.dp_engine = self.dp_engine

            update, metrics = client.local_train_with_metrics(
                global_model, local_epochs, lr
            )
            client_updates.append(update)
            client_sizes.append(client.dataset_size)
            client_metrics.append(metrics)

        # Aggregate updates
        self.coordinator.aggregate(client_updates, client_sizes)

        # Apply DP to aggregated model if using global DP
        privacy_spent = None
        if self.dp_engine and not self.dp_engine.use_opacus:
            privacy_spent = self._apply_global_dp()

        # Get evaluation metrics
        eval_metrics = self.evaluate_with_metrics()

        # Aggregate client metrics
        avg_client_accuracy = sum(m["accuracy"] for m in client_metrics) / len(
            client_metrics
        )
        avg_client_loss = sum(m["loss"] for m in client_metrics) / len(client_metrics)

        round_metrics = {
            "accuracy": eval_metrics["accuracy"],
            "loss": eval_metrics["loss"],
            "client_accuracy": avg_client_accuracy,
            "client_loss": avg_client_loss,
            "privacy_spent": privacy_spent or self._get_privacy_status(),
            "num_clients": len(client_indices),
            "samples": sum(client_sizes),
        }

        return round_metrics

    def _apply_global_dp(self) -> dict:
        """
        Apply DP to aggregated global model updates
        """
        global_model = self.coordinator.get_global_model()

        # Get current global parameters
        current_params = {k: v.clone() for k, v in global_model.state_dict().items()}

        # Add noise to model parameters
        if self.dp_engine:
            noisy_params = self.dp_engine.add_noise_to_updates(current_params)

            # Update global model with noisy parameters
            global_model.load_state_dict(noisy_params)

            # Track privacy spending
            privacy_spent = self.dp_engine.get_privacy_spent()
            self.total_privacy_spent = privacy_spent

            logger.info(
                f"Global DP applied - Privacy spent: ε={privacy_spent['epsilon']:.4f}"
            )

            return privacy_spent

        return None

    def _get_privacy_status(self) -> dict:
        """
        Get current privacy budget status
        """
        if self.dp_engine:
            return {
                "total_epsilon": self.dp_engine.get_privacy_spent()["epsilon"],
                "remaining_epsilon": max(
                    0,
                    self.dp_engine.epsilon
                    - self.dp_engine.get_privacy_spent()["epsilon"],
                ),
                "delta": self.dp_engine.delta,
                "rounds_completed": self.dp_engine.rounds_completed,
            }
        return {"enabled": False}

    def evaluate(self) -> float:
        """Evaluate model accuracy"""
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

                test_loss += criterion(output, target).item()
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
            return torch.nn.CrossEntropyLoss()
