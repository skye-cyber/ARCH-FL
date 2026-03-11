from pydantic import BaseModel
from typing import Any, Optional, Dict


class ExperimentCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    dataset_name: str
    architecture_name: str
    num_clients: int
    iid: bool
    parameters: Dict[str, Any]


class ExperimentUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]
    status: Optional[str]
    parameters: Optional[Dict[str, Any]]
