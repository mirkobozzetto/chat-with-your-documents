# src/chat_history/__init__.py
"""
Chat History System

Interface-agnostic conversation persistence and management:
- SessionManager: Current conversation state management
- ConversationHistoryManager: Historical conversation operations
- BaseConversationStorage: Storage interface (JSON, SQLite, etc.)
- Models: Conversation, ChatMessage, ConversationMetadata
- Adapters: Interface-specific implementations (Streamlit, API, CLI)
"""

from .models import Conversation, ChatMessage, ConversationMetadata, ConversationSummary
from .session_manager import SessionManager, ConversationHistoryManager
from .storage.base_storage import BaseConversationStorage
from .storage.json_storage import JsonConversationStorage

__all__ = [
    'Conversation',
    'ChatMessage',
    'ConversationMetadata',
    'ConversationSummary',
    'SessionManager',
    'ConversationHistoryManager',
    'BaseConversationStorage',
    'JsonConversationStorage'
]

__version__ = '1.0.0'
