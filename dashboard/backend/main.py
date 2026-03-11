"""
ARCH-FL Dashboard Backend - FastAPI Application

Main application entry point with API endpoints for the dashboard.
"""

# from fastapi.responses import HTMLResponse
import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from .db import dbmanager
from .utils.logger import logger
from .config.settings import settings
from .api.routes import (
    architecture_router,
    experiments_router,
    websockets_router,
    datasets_router,
    system_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    logger.info("=" * 50)
    logger.info(f"Starting ARCH-FL API v{settings.API_VERSION}")
    logger.info(f"Environment: {'development' if settings.DEBUG else 'production'}")
    logger.info(f"Host: {settings.HOST}:{settings.PORT}")
    # Initialize database on startup
    dbmanager.init()
    logger.info("=" * 50)

    yield

    # Shutdown
    logger.info("Shutting down ARCH-FL API...")
    # await cleanup_resources()
    logger.info("Shutdown complete")


# Initialize FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.ALLOW_CREDENTIALS,
    allow_methods=settings.ALLOWED_METHODS,
    allow_headers=settings.ALLOWED_HEADERS,
    max_age=settings.CACHE_TTL,
)

# Include routers
app.include_router(experiments_router, prefix=settings.API_V1_PREFIX)
app.include_router(architecture_router, prefix=settings.API_V1_PREFIX)
app.include_router(datasets_router, prefix=settings.API_V1_PREFIX)
app.include_router(system_router, prefix=settings.API_V1_PREFIX)
app.include_router(websockets_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": settings.API_TITLE,
        "version": settings.API_VERSION,
        "description": settings.API_DESCRIPTION,
        "docs": "/docs" if settings.DEBUG else None,
        "health": "/api/v1/system/health",
        "status": "running",
    }


def start():
    """Start the server using uvicorn"""
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        workers=settings.WORKERS,
        log_level=settings.LOG_LEVEL.lower(),
    )


if __name__ == "__main__":
    start()
