# src/chat_history/storage/base_storage.py
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from ..models import Conversation, ConversationSummary


class BaseConversationStorage(ABC):

    @abstractmethod
    def save_conversation(self, conversation: Conversation) -> None:
        pass

    @abstractmethod
    def load_conversation(self, session_id: str) -> Optional[Conversation]:
        pass

    @abstractmethod
    def delete_conversation(self, session_id: str) -> bool:
        pass

    @abstractmethod
    def list_conversations(self, limit: Optional[int] = None,
                          offset: int = 0) -> List[ConversationSummary]:
        pass

    @abstractmethod
    def search_conversations(self, query: str, limit: Optional[int] = None) -> List[ConversationSummary]:
        pass

    @abstractmethod
    def get_conversations_by_document(self, document_name: str) -> List[ConversationSummary]:
        pass

    @abstractmethod
    def get_conversations_by_agent(self, agent_type: str) -> List[ConversationSummary]:
        pass

    @abstractmethod
    def get_conversation_count(self) -> int:
        pass

    @abstractmethod
    def cleanup_old_conversations(self, days_threshold: int = 30) -> int:
        pass

    @abstractmethod
    def export_conversation(self, session_id: str, format: str = "json") -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def import_conversation(self, conversation_data: Dict[str, Any]) -> bool:
        pass
