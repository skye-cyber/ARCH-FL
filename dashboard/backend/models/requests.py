from pydantic import BaseModel
from typing import Any, Optional, Dict, List


class ArchitectureCreate(BaseModel):
    name: str
    description: str = ""
    config: Dict[str, Any]
    compatible_datasets: Optional[List[str]] = []


class ExperimentCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    dataset_name: str
    architecture_name: str
    num_clients: int
    iid: bool
    parameters: Dict[str, Any]
    dp_enabled: bool = False
    # Privacy Budget
    epsilon: float = None
    # Privacy Failure Probability
    delta: float = None
    # noise_scale: float = None
    # sensitivity: float = None
    max_grad_norm: float = None
    # gaussian or laplace
    noise_mechanism: str = "gaussian"


class ExperimentUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]
    status: Optional[str]
    parameters: Optional[Dict[str, Any]]
    dp_enabled: bool = False
    # Privacy Budget
    epsilon: float = None
    # Privacy Failure Probability
    delta: float = None
    # For gaussian or laplace noise
    noise_scale: float = None
    sensitivity: float = None
    max_grad_norm: float = None
    # gaussian or laplace
    noise_mechanism: str = None
