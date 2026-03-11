from pydantic import BaseModel
from typing import Any, Optional, Dict, List


class ArchitectureCreate(BaseModel):
    name: str
    description: str = ""
    config: Dict[str, Any]
    compatible_datasets: Optional[List[str]] = []
