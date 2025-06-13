# ui/components/__init__.py
"""
UI Components Package

Contains specialized UI components:
- DocumentManagement: Document upload and selection
- KnowledgeBaseStats: Statistics display
- ChatInterface: Conversation management
"""

from .document_management import DocumentManagement
from .knowledge_base_stats import KnowledgeBaseStats
from .chat_interface import ChatInterface

__all__ = [
    'DocumentManagement',
    'KnowledgeBaseStats',
    'ChatInterface'
]
