"""smspanel application factory.

This module provides the app factory pattern.
"""

from .app import create_app
from .extensions import db, login_manager

__all__ = ["create_app", "db", "login_manager"]
