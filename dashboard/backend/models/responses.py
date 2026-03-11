from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class ExperimentStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExperimentResponse(BaseModel):
    """Response model for task submission"""

    task_id: str
    status: ExperimentStatus
    message: str
    created_at: str

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "pending",
                "message": "Experiment submitted successfully",
                "created_at": "2026-01-15T10:30:00",
            }
        }


class ExperimentStatusResponse(BaseModel):
    """Response model for task status queries"""

    task_id: str
    status: ExperimentStatus
    progress: int = Field(..., ge=0, le=100)
    message: str
    logs: List[str]
    created_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "running",
                "progress": 45,
                "message": "Processing iteration 5 of 10",
                "logs": ["[10:30:05] Started processing", "[10:30:10] Page 1 complete"],
                "created_at": "2026-01-15T10:30:00",
                "started_at": "2026-01-15T10:30:01",
            }
        }


class OperationResult(BaseModel):
    """Response model for operation results"""

    success: bool
    message: str
    output_path: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    execution_time: Optional[float] = None

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Experiment completed successfully",
                "output_path": "/outputs/20260115/experiment_124.json",
                "execution_time": 3.45,
            }
        }


class ErrorResponse(BaseModel):
    """Response model for errors"""

    error: str
    detail: Optional[str] = None
    status_code: int
    timestamp: str
    path: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "error": "Experiment failed",
                "detail": "memory pressre",
                "status_code": 500,
                "timestamp": "2026-03-15T10:30:00",
                "path": "/api/v1/experiment/run",
            }
        }


class SystemInfoResponse(BaseModel):
    """Response model for system information"""

    version: str
    api_version: str
    uptime: str
    active_tasks: int
    completed_tasks: int
    failed_tasks: int
    total_tasks: int
    system_info: Dict[str, Any]

    class Config:
        json_schema_extra = {
            "example": {
                "version": "1.0.0",
                "api_version": "v1",
                "uptime": "2 days, 3 hours",
                "active_tasks": 2,
                "completed_tasks": 150,
                "failed_tasks": 3,
                "total_tasks": 155,
                "system_info": {
                    "cpu_count": 8,
                    "memory_total": "16 GB",
                    "disk_free": "50 GB",
                },
            }
        }
