"""
Data Loaders Module

This module provides the original get_data_loaders function for backward compatibility.
The new registry-based system is implemented in loader_registry.py
"""

from .loader_registry import get_data_loaders

# The original get_data_loaders function is now implemented in loader_registry.py
# This maintains backward compatibility while using the new registry system
