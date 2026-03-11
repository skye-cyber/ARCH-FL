import psutil, sys
from fastapi import APIRouter
from datetime import datetime

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}
