import torch.nn as nn
import torch
from src.data.partitioning import partition_iid
from src.core.client import Client
from src.core.coordinator import Coordinator
from config import Config
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


class SimpleCNN(nn.Module):
    def __init__(self, num_classes=2):
        super().__init__()
        self.conv1 = nn.Conv2d(1, 32, 3, 1)
        self.conv2 = nn.Conv2d(32, 64, 3, 1)
        self.fc1 = nn.Linear(9216, 128)
        self.fc2 = nn.Linear(128, num_classes)

    def forward(self, x):
        x = torch.relu(self.conv1(x))
        x = torch.relu(self.conv2(x))
        x = torch.flatten(x, 1)
        x = torch.relu(self.fc1(x))
        return self.fc2(x)


def main():
    config = Config('config/experiment/iid_baseline.yaml')
    print("Running baseline experiment...")

    # Initialize model
    model = SimpleCNN()
    coordinator = Coordinator(model)

    print("Baseline setup complete. Ready for federated training.")


if __name__ == "__main__":
    main()
