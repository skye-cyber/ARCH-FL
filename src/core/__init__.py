"""Core module for ARCH-FL project"""

from .coordinator import Coordinator
from .client import Client
from .aggregation import fed_avg, weighted_aggregation, secure_aggregation

__all__ = [
    "Coordinator",
    "Client",
    "fed_avg",
    "weighted_aggregation",
    "secure_aggregation",
]
