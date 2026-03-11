from .architectures import router as architecture_router
from .experiments import router as experiments_router
from .datasets import router as datasets_router
from .system import router as system_router
from .websocket import router as websockets_router


__all__ = [
    "architecture_router",
    "websockets_router",
    "experiments_router",
    "datasets_router",
    "system_router",
]
