# src/auth/__init__.py
"""
Authentication system

Provides user authentication and session management:
- AuthManager: File-based authentication (legacy)
- DBAuthManager: Database-based authentication (recommended)
- AuthConfig: Configuration and user management
"""

from .auth_manager import AuthManager
from .db_auth_manager import DBAuthManager
from .auth_config import AuthConfig

__all__ = [
    'AuthManager',
    'DBAuthManager',
    'AuthConfig'
]
