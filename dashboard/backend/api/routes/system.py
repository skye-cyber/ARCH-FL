import platform
import psutil
import time
import math
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query
from backend.core.experiment_manager import ExperimentManager
from backend.services.progress import ProgressService
from backend.api.dependencies import get_experiment_manager, get_progress_service
from backend.models.responses import SystemInfoResponse
from backend.utils.logger import logger
from backend.config.settings import settings
from backend import __version__

router = APIRouter(prefix="/system", tags=["system"])

# Track server start time
SERVER_START_TIME = time.time()


@router.get("/status")
async def get_system_status(
    task_manager: ExperimentManager = Depends(get_experiment_manager),
    progress_service: ProgressService = Depends(get_progress_service),
):
    """
    Get system status and statistics
    """
    try:
        # Get task statistics from task manager
        task_stats = task_manager.get_statistics()

        # Get progress statistics
        progress_stats = progress_service.get_statistics()

        # Get system info
        uptime_seconds = time.time() - SERVER_START_TIME
        uptime_str = str(timedelta(seconds=int(uptime_seconds)))

        return {
            "status": "operational",
            "uptime": uptime_str,
            "uptime_seconds": uptime_seconds,
            "tasks": task_stats,
            "progress": progress_stats,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/info", response_model=SystemInfoResponse)
async def get_system_info():
    """
    Get detailed system information
    """
    try:
        # System info
        system_info = {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "processor": platform.processor(),
            "machine": platform.machine(),
            "hostname": platform.node(),
        }

        # CPU info
        cpu_info = {
            "count": psutil.cpu_count(),
            "physical_count": psutil.cpu_count(logical=False),
            "percent": psutil.cpu_percent(interval=1),
            "frequency": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
        }

        # Memory info
        memory = psutil.virtual_memory()
        memory_info = {
            "total": memory.total,
            "total_human": f"{memory.total / (1024**3):.2f} GB",
            "available": memory.available,
            "available_human": f"{memory.available / (1024**3):.2f} GB",
            "percent": memory.percent,
            "used": memory.used,
            "used_human": f"{memory.used / (1024**3):.2f} GB",
        }

        # Disk info
        disk = psutil.disk_usage("/")
        disk_info = {
            "total": disk.total,
            "total_human": f"{disk.total / (1024**3):.2f} GB",
            "used": disk.used,
            "used_human": f"{disk.used / (1024**3):.2f} GB",
            "free": disk.free,
            "free_human": f"{disk.free / (1024**3):.2f} GB",
            "percent": disk.percent,
        }

        # Uptime
        uptime_seconds = time.time() - SERVER_START_TIME
        uptime_str = str(timedelta(seconds=int(uptime_seconds)))

        return SystemInfoResponse(
            version=__version__,
            api_version="v1",
            uptime=uptime_str,
            active_tasks=0,  # Will be filled by caller
            completed_tasks=0,  # Will be filled by caller
            failed_tasks=0,  # Will be filled by caller
            total_tasks=0,  # Will be filled by caller
            system_info={
                "system": system_info,
                "cpu": cpu_info,
                "memory": memory_info,
                "disk": disk_info,
                "network": "-",
            },
        )

    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """
    Simple health check endpoint
    """
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@router.get("/version")
async def get_version():
    """
    Get API version information
    """
    return {
        "api_version": "v1",
        "backend_version": settings.API_VERSION,
        "archfl_version": __version__,  # Should be imported from filewarp
        "build_date": "-",
        "dependencies": {
            "python": platform.python_version(),
            "fastapi": "-",
        },
    }


@router.get("/metrics")
async def get_metrics(
    task_manager: ExperimentManager = Depends(get_experiment_manager),
    progress_service: ProgressService = Depends(get_progress_service),
):
    """
    Get detailed system metrics for monitoring
    """
    try:
        # Task metrics
        task_stats = task_manager.get_statistics()

        # Progress metrics
        progress_stats = progress_service.get_statistics()

        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        return {
            "timestamp": datetime.now().isoformat(),
            "system": {
                "cpu": {
                    "unit": "percentage",
                    "overall": psutil.cpu_percent(interval=1),
                    "per_cpu": cpu_percent,
                    "load_avg": [
                        x / psutil.cpu_count() * 100 for x in psutil.getloadavg()
                    ]
                    if hasattr(psutil, "getloadavg")
                    else None,
                },
                "memory": {
                    "unit": "MB",
                    "total": math.floor(memory.total / 1048576),
                    "available": math.floor(memory.available / 1048576),
                    "percent": memory.percent,
                    "used": math.floor(memory.used / 1048576),
                },
                "disk": {
                    "unit": "GB",
                    "total": math.floor(disk.total / 1073741824),
                    "used": math.floor(disk.used / 1073741824),
                    "free": math.floor(disk.free / 1073741824),
                    "percent": disk.percent,
                },
            },
            "tasks": task_stats,
            "progress": progress_stats,
        }

    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/shutdown")
async def shutdown_server(
    force: bool = Query(
        False, description="Force shutdown even with active experiments"
    ),
):
    """
    Shutdown the server (admin only)
    """
    # This would typically require authentication
    logger.warning(f"Shutdown requested (force={force})")

    return {
        "message": "Shutdown initiated",
        "force": force,
        "timestamp": datetime.now().isoformat(),
    }


@router.post("/cleanup")
async def cleanup_system(
    days: int = Query(7, description="Delete tasks older than X days", ge=1, le=30),
    task_manager: ExperimentManager = Depends(get_experiment_manager),
):
    """
    Clean up old tasks and temporary files
    """
    try:
        # Clean up old tasks from memory
        task_count = task_manager.cleanup_old_tasks(days=days)

        # Clean up temp files (implement based on your temp file strategy)
        temp_count = 0  # Placeholder

        return {
            "message": "Cleanup completed",
            "tasks_removed": task_count,
            "temp_files_removed": temp_count,
            "days": days,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs")
async def get_logs(
    level: str = Query("INFO", enum=["DEBUG", "INFO", "WARNING", "ERROR"]),
    lines: int = Query(100, description="Number of log lines", ge=10, le=1000),
):
    """
    Get recent log entries
    """
    log_lines = ""
    log_file = settings.LOG_DIR / settings.LOG_FILE
    if log_file.exists():
        with open(log_file, "r") as f:
            log_lines = f.readline(lines)

    return {
        "level": settings.LOG_LEVEL,
        "lines_requested": lines,
        "logs": log_lines,
    }


@router.get("/config")
async def get_configuration():
    """
    Get current system configuration
    """
    return {
        "max_concurrent_tasks": settings.WORKERS,
        "task_timeout": settings.CACHE_TTL,
        "features": {
            "websocket_support": True,
            "batch_processing": True,
            "progress_tracking": True,
            "notifications": True,
        },
    }
