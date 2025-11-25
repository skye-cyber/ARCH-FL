import torch
from src.models.architectures import SimpleCNN
from src.data.loaders import get_data_loaders
from src.training.fedavg import FederatedTrainer
from src.core.client import Client
from src.core.coordinator import Coordinator
from config import Config
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


def main():
    config = Config('config/experiment/iid_baseline.yaml')

    # Setup
    device = "cuda" if torch.cuda.is_available() else "cpu"
    client_loaders, test_loader = get_data_loaders(
        config.get('data.dataset'),
        config.get('data.num_clients'),
        config.get('data.iid')
    )

    # Initialize model and coordinator
    model = SimpleCNN().to(device)
    coordinator = Coordinator(model)

    # Create clients
    clients = [
        Client(i, SimpleCNN().to(device), loader, device)
        for i, loader in enumerate(client_loaders)
    ]

    # Train
    trainer = FederatedTrainer(coordinator, clients, test_loader, device)

    for round_num in range(config.get('experiment.default_rounds')):
        client_indices = list(range(len(clients)))
        accuracy = trainer.train_round(
            client_indices,
            config.get('training.local_epochs'),
            config.get('training.learning_rate')
        )

        if (round_num + 1) % config.get('experiment.eval_interval') == 0:
            print(f"Round {round_num + 1}: Accuracy = {accuracy:.2f}%")


if __name__ == "__main__":
    main()
