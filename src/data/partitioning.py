import numpy as np
from typing import List, Tuple
import torch
from torch.utils.data import Subset


def partition_iid(dataset, num_clients: int) -> List[Subset]:
    num_samples = len(dataset) // num_clients
    indices = np.random.permutation(len(dataset))
    return [Subset(dataset, indices[i * num_samples:(i + 1) * num_samples])
            for i in range(num_clients)]


def partition_non_iid(dataset, num_clients: int, alpha: float = 0.5) -> List[Subset]:
    num_classes = len(dataset.classes) if hasattr(dataset, 'classes') else 10
    labels = np.array([dataset[i][1] for i in range(len(dataset))])

    # Dirichlet distribution
    label_distribution = np.random.dirichlet([alpha] * num_clients, num_classes)
    class_idx = [np.where(labels == i)[0] for i in range(num_classes)]

    client_indices = [[] for _ in range(num_clients)]
    for c, indices in enumerate(class_idx):
        proportions = label_distribution[c]
        proportions = proportions / proportions.sum()
        splits = (np.cumsum(proportions) * len(indices)).astype(int)[:-1]
        for i, idx in enumerate(np.split(indices, splits)):
            client_indices[i].extend(idx)

    return [Subset(dataset, indices) for indices in client_indices]
