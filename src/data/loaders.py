from torch.utils.data import DataLoader, random_split
from .partitioning import partition_iid, partition_non_iid
from .datasets import MedicalDataset, get_transform
import numpy as np


def get_data_loaders(dataset_name: str, num_clients: int, iid: bool = True,
                     batch_size: int = 32, alpha: float = 0.5) -> tuple:

    # For now, use synthetic data - replace with MedMNIST later
    if dataset_name == "PneumoniaMNIST":
        num_samples = 1000
        data = np.random.randn(num_samples, 1, 28, 28).astype(np.float32)
        targets = np.random.randint(0, 2, num_samples)
    else:
        raise ValueError(f"Unsupported dataset: {dataset_name}")

    dataset = MedicalDataset(data, targets, transform=get_transform())

    if iid:
        client_datasets = partition_iid(dataset, num_clients)
    else:
        client_datasets = partition_non_iid(dataset, num_clients, alpha)

    client_loaders = []
    for client_dataset in client_datasets:
        loader = DataLoader(client_dataset, batch_size=batch_size, shuffle=True)
        client_loaders.append(loader)

    # Create test loader (20% of data)
    train_size = int(0.8 * len(dataset))
    test_size = len(dataset) - train_size
    train_dataset, test_dataset = random_split(dataset, [train_size, test_size])
    test_loader = DataLoader(test_dataset, batch_size=batch_size)

    return client_loaders, test_loader
