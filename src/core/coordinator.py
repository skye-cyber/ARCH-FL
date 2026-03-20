import torch
from typing import List, Dict, Optional, Callable
from .aggregation import fed_avg, weighted_aggregation, secure_aggregation

# from ..utils.logger import logger
from ..utils.model_utils import unwrap_dp_state_dict

# Type definition for progress callback
ProgressCallback = Callable[[int, Dict[str, float], str], None]


class Coordinator:
    def __init__(
        self,
        model: torch.nn.Module,
        aggregation_method: str = "fed_avg",
        progress_callback: Optional[ProgressCallback] = None,
    ):
        self.global_model = model
        self.aggregation_method = aggregation_method
        self.aggregation_fns = {
            "fed_avg": fed_avg,
            "weighted": weighted_aggregation,
            "secure": secure_aggregation,
        }
        self.progress_callback = progress_callback

    def aggregate(
        self,
        client_updates: List[Dict[str, torch.Tensor]],
        client_sizes: List[int],
        weights: List[float] = None,
        round_num: Optional[int] = None,
    ) -> None:

        if self.aggregation_method == "weighted" and weights is None:
            raise ValueError("Weights required for weighted aggregation")

        agg_fn = self.aggregation_fns[self.aggregation_method]

        if self.aggregation_method == "weighted":
            averaged_params = agg_fn(client_updates, weights)
        else:
            averaged_params = agg_fn(client_updates, client_sizes)

        averaged_params = unwrap_dp_state_dict(averaged_params)

        self.global_model.load_state_dict(averaged_params)
        # logger.info(f"Aggregated {len(client_updates)} clients using {self.aggregation_method}")

        # Call progress callback if provided
        if self.progress_callback and round_num is not None:
            metrics = {
                "num_clients": len(client_updates),
                "aggregation_method": self.aggregation_method,
            }
            self.progress_callback(round_num, metrics, "aggregation_complete")

    def get_global_model(self) -> Dict[str, torch.Tensor]:
        return self.global_model.state_dict()

    def get_model_summary(self) -> Dict[str, any]:
        """Get a summary of the global model for dashboard display."""
        model_summary = {
            "num_parameters": sum(p.numel() for p in self.global_model.parameters()),
            "num_layers": len(list(self.global_model.children())),
            "aggregation_method": self.aggregation_method,
            "model_type": type(self.global_model).__name__,
        }
        return model_summary

    def set_aggregation_method(self, method: str):
        if method not in self.aggregation_fns:
            raise ValueError(f"Unknown aggregation method: {method}")
        self.aggregation_method = method
