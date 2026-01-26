import numpy as np
from typing import List, Tuple
import torch
from torch.utils.data import Subset


def partition_iid(dataset, num_clients: int) -> List[Subset]:
    """
    Partition dataset into IID subsets for federated learning.
    
    Args:
        dataset: PyTorch dataset to partition
        num_clients: Number of client partitions to create
        
    Returns:
        List of Subset objects, one for each client
    """
    indices = np.random.permutation(len(dataset))
    
    # Distribute samples as evenly as possible
    num_samples_per_client = len(dataset) // num_clients
    remainder = len(dataset) % num_clients
    
    client_indices = []
    start = 0
    for i in range(num_clients):
        # Give extra samples to first 'remainder' clients
        extra = 1 if i < remainder else 0
        end = start + num_samples_per_client + extra
        client_indices.append(indices[start:end])
        start = end
    
    return [Subset(dataset, indices) for indices in client_indices]


def partition_non_iid(dataset, num_clients: int, alpha: float = 0.5) -> List[Subset]:
    """
    Partition dataset into non-IID subsets using Dirichlet distribution.
    
    Args:
        dataset: PyTorch dataset to partition
        num_clients: Number of client partitions to create
        alpha: Parameter for Dirichlet distribution (lower = more non-IID)
        
    Returns:
        List of Subset objects, one for each client
    """
    # Get labels from dataset
    try:
        num_classes = len(dataset.classes) if hasattr(dataset, 'classes') else 2
        labels = np.array([dataset[i][1] for i in range(len(dataset))])
    except (IndexError, AttributeError):
        # If dataset doesn't have proper structure, create synthetic labels
        num_classes = 2
        labels = np.random.randint(0, num_classes, len(dataset))

    # Ensure we have at least one sample per class per client for extreme cases
    min_samples_per_client = max(1, len(dataset) // (num_clients * num_classes * 10))
    
    # Dirichlet distribution for class proportions
    label_distribution = np.random.dirichlet([alpha] * num_clients, num_classes)
    class_idx = [np.where(labels == i)[0] for i in range(num_classes)]

    client_indices = [[] for _ in range(num_clients)]
    
    for c, indices in enumerate(class_idx):
        if len(indices) == 0:
            continue
            
        proportions = label_distribution[c]
        proportions = proportions / proportions.sum()
        
        # Ensure each client gets at least min_samples_per_client samples from this class
        min_samples = min(min_samples_per_client, len(indices) // num_clients)
        
        # Calculate splits with minimum samples guarantee
        remaining_samples = len(indices) - min_samples * num_clients
        if remaining_samples > 0:
            # Distribute remaining samples proportionally
            extra_proportions = remaining_samples * proportions
            extra_samples = np.round(extra_proportions).astype(int)
            # Adjust for rounding errors
            extra_samples[-1] += remaining_samples - extra_samples.sum()
        else:
            extra_samples = np.zeros(num_clients, dtype=int)
        
        # Create splits
        splits = []
        start = 0
        for i in range(num_clients):
            client_samples = min_samples + extra_samples[i]
            end = start + client_samples
            client_indices[i].extend(indices[start:end])
            start = end

    # Ensure all clients have at least one sample
    for i in range(num_clients):
        if len(client_indices[i]) == 0 and len(dataset) > num_clients:
            # Assign one random sample to this client
            remaining_indices = set(range(len(dataset))) - set().union(*[set(idx) for idx in client_indices])
            if remaining_indices:
                client_indices[i].append(np.random.choice(list(remaining_indices)))

    return [Subset(dataset, indices) for indices in client_indices]
