"""
Backend-specific configuration.

This module provides a wrapper around the global settings
to add backend-specific configuration if needed.
"""

import sys
from pathlib import Path

# Add project root to path so we can import from config module
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from config import Settings  # noqa: E402
from config import settings as global_settings  # noqa: E402


def get_settings() -> Settings:
    """
    Get the global settings instance.

    This function is used for dependency injection in FastAPI routes.
    It allows easy mocking in tests.

    Returns:
        Settings: The global settings instance
    """
    return global_settings


__all__ = ["get_settings", "Settings"]
