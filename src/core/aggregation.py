import torch
from typing import List, Dict
from ..utils.logger import get_logger

logger = get_logger(__name__)


def fed_avg(client_updates: List[Dict[str, torch.Tensor]],
            client_sizes: List[int]) -> Dict[str, torch.Tensor]:
    """Federated Averaging aggregation"""
    total_size = sum(client_sizes)
    averaged_params = {}

    for key in client_updates[0].keys():
        weighted_sum = torch.zeros_like(client_updates[0][key])
        for i, update in enumerate(client_updates):
            weight = client_sizes[i] / total_size
            weighted_sum += update[key] * weight
        averaged_params[key] = weighted_sum

    logger.debug(f"FedAvg completed for {len(client_updates)} clients")
    return averaged_params


def weighted_aggregation(client_updates: List[Dict[str, torch.Tensor]],
                         weights: List[float]) -> Dict[str, torch.Tensor]:
    """Custom weighted aggregation"""
    averaged_params = {}

    for key in client_updates[0].keys():
        weighted_sum = torch.zeros_like(client_updates[0][key])
        for i, update in enumerate(client_updates):
            weighted_sum += update[key] * weights[i]
        averaged_params[key] = weighted_sum

    logger.debug(f"Weighted aggregation with custom weights for {len(client_updates)} clients")
    return averaged_params


def secure_aggregation(client_updates: List[Dict[str, torch.Tensor]],
                       client_sizes: List[int]) -> Dict[str, torch.Tensor]:
    """Placeholder for secure aggregation with masking"""
    # Implementation would add cryptographic masking here
    logger.info("Using secure aggregation (masking)")
    return fed_avg(client_updates, client_sizes)
