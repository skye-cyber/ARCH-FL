"""
ARCH-FL Backend API
A REST API backend for ARCH-FL operations with async task management and real-time updates.
"""

__version__ = "1.0.0"
__author__ = "ARCH-FL Team"
__license__ = "MIT"

from .main import app

__all__ = ["app"]
