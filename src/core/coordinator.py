import torch
from typing import List, Dict
from .aggregation import fed_avg, weighted_aggregation, secure_aggregation
from ..utils.logger import get_logger

logger = get_logger(__name__)


class Coordinator:
    def __init__(self, model: torch.nn.Module, aggregation_method: str = "fed_avg"):
        self.global_model = model
        self.aggregation_method = aggregation_method
        self.aggregation_fns = {
            "fed_avg": fed_avg,
            "weighted": weighted_aggregation,
            "secure": secure_aggregation
        }

    def aggregate(self, client_updates: List[Dict[str, torch.Tensor]],
                  client_sizes: List[int], weights: List[float] = None) -> None:

        if self.aggregation_method == "weighted" and weights is None:
            raise ValueError("Weights required for weighted aggregation")

        agg_fn = self.aggregation_fns[self.aggregation_method]

        if self.aggregation_method == "weighted":
            averaged_params = agg_fn(client_updates, weights)
        else:
            averaged_params = agg_fn(client_updates, client_sizes)

        self.global_model.load_state_dict(averaged_params)
        logger.info(f"Aggregated {len(client_updates)} clients using {self.aggregation_method}")

    def get_global_model(self) -> Dict[str, torch.Tensor]:
        return self.global_model.state_dict()

    def set_aggregation_method(self, method: str):
        if method not in self.aggregation_fns:
            raise ValueError(f"Unknown aggregation method: {method}")
        self.aggregation_method = method
