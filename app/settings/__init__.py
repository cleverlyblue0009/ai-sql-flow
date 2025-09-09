"""
Settings and configuration management module
"""

from .routes import router
from .settings_service import SettingsService

__all__ = ["router", "SettingsService"]