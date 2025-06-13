# ui/__init__.py
"""
UI Package for RAG System

Contains modular UI components following SRP:
- SessionManager: Streamlit state management
- FileHandler: File operations
- Components: UI rendering modules
"""

from .session_manager import SessionManager
from .file_handler import FileHandler

__all__ = [
    'SessionManager',
    'FileHandler'
]

__version__ = '1.0.0'
