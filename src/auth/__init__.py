# src/auth/__init__.py
"""
Authentication system

Provides user authentication and session management:
- AuthManager: Database-based authentication
- AuthConfig: Configuration and user management
"""

from .auth_manager import AuthManager
from .auth_config import AuthConfig

__all__ = [
    'AuthManager',
    'AuthConfig'
]
