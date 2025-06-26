# src/chat_history/session_manager.py
from typing import Optional, Dict, Any, Callable
from .models import Conversation, ConversationMetadata
from .storage.base_storage import BaseConversationStorage
from .storage.postgres_storage import PostgresConversationStorage


class SessionManager:

    def __init__(self, storage: Optional[BaseConversationStorage] = None):
        self.storage = storage or PostgresConversationStorage()
        self.current_session: Optional[Conversation] = None
        self.auto_save = True
        self.on_session_change: Optional[Callable[[Optional[Conversation]], None]] = None

    def create_new_session(self, title: str = "New Conversation",
                          **metadata_kwargs) -> Conversation:
        self.current_session = Conversation.create_new(title=title, **metadata_kwargs)

        if self.auto_save:
            self.storage.save_conversation(self.current_session)

        if self.on_session_change:
            self.on_session_change(self.current_session)

        return self.current_session

    def load_session(self, session_id: str) -> Optional[Conversation]:
        conversation = self.storage.load_conversation(session_id)
        if conversation:
            self.current_session = conversation
            if self.on_session_change:
                self.on_session_change(self.current_session)
        return conversation

    def get_current_session(self) -> Optional[Conversation]:
        return self.current_session

    def add_message(self, role: str, content: str, metadata: Dict[str, Any] = None) -> None:
        if not self.current_session:
            self.create_new_session()

        self.current_session.add_message(role, content, metadata)

        if self.auto_save:
            self.storage.save_conversation(self.current_session)

    def update_session_metadata(self, **kwargs) -> None:
        if self.current_session:
            self.current_session.update_metadata(**kwargs)

            if self.auto_save:
                self.storage.save_conversation(self.current_session)

    def set_session_title(self, title: str) -> None:
        if self.current_session:
            self.current_session.title = title

            if self.auto_save:
                self.storage.save_conversation(self.current_session)

    def end_current_session(self) -> None:
        if self.current_session and self.auto_save:
            self.storage.save_conversation(self.current_session)

        self.current_session = None

        if self.on_session_change:
            self.on_session_change(None)

    def delete_session(self, session_id: str) -> bool:
        success = self.storage.delete_conversation(session_id)

        if success and self.current_session and self.current_session.session_id == session_id:
            self.current_session = None
            if self.on_session_change:
                self.on_session_change(None)

        return success

    def get_session_id(self) -> Optional[str]:
        return self.current_session.session_id if self.current_session else None

    def has_active_session(self) -> bool:
        return self.current_session is not None

    def get_message_count(self) -> int:
        return self.current_session.message_count if self.current_session else 0

    def get_messages(self) -> list:
        if self.current_session:
            return [
                {"role": msg.role, "content": msg.content, "timestamp": msg.timestamp}
                for msg in self.current_session.messages
            ]
        return []

    def get_messages_for_context(self, last_n: int = 6) -> list:
        messages = self.get_messages()
        return messages[-last_n:] if len(messages) > last_n else messages

    def clear_current_session_messages(self) -> None:
        if self.current_session:
            self.current_session.messages = []

            if self.auto_save:
                self.storage.save_conversation(self.current_session)

    def set_auto_save(self, enabled: bool) -> None:
        self.auto_save = enabled

    def force_save_current_session(self) -> None:
        if self.current_session:
            self.storage.save_conversation(self.current_session)

    def set_session_change_callback(self, callback: Callable[[Optional[Conversation]], None]) -> None:
        self.on_session_change = callback

    def get_storage(self) -> BaseConversationStorage:
        return self.storage


class ConversationHistoryManager:

    def __init__(self, storage: Optional[BaseConversationStorage] = None):
        self.storage = storage or PostgresConversationStorage()

    def list_recent_conversations(self, limit: int = 20) -> list:
        summaries = self.storage.list_conversations(limit=limit)
        return [
            {
                "session_id": summary.session_id,
                "title": summary.title,
                "message_count": summary.message_count,
                "last_activity": summary.last_activity,
                "document_name": summary.document_name,
                "agent_type": summary.agent_type
            }
            for summary in summaries
        ]

    def search_conversations(self, query: str, limit: int = 10) -> list:
        summaries = self.storage.search_conversations(query, limit)
        return [
            {
                "session_id": summary.session_id,
                "title": summary.title,
                "message_count": summary.message_count,
                "last_activity": summary.last_activity,
                "document_name": summary.document_name,
                "agent_type": summary.agent_type
            }
            for summary in summaries
        ]

    def get_conversations_by_document(self, document_name: str) -> list:
        summaries = self.storage.get_conversations_by_document(document_name)
        return [
            {
                "session_id": summary.session_id,
                "title": summary.title,
                "message_count": summary.message_count,
                "last_activity": summary.last_activity
            }
            for summary in summaries
        ]

    def export_conversation(self, session_id: str) -> Optional[Dict[str, Any]]:
        return self.storage.export_conversation(session_id)

    def import_conversation(self, conversation_data: Dict[str, Any]) -> bool:
        return self.storage.import_conversation(conversation_data)

    def delete_conversation(self, session_id: str) -> bool:
        return self.storage.delete_conversation(session_id)

    def get_statistics(self) -> Dict[str, Any]:
        return {
            "total_conversations": self.storage.get_conversation_count(),
            "recent_conversations": len(self.storage.list_conversations(limit=7)),
        }

    def cleanup_old_conversations(self, days_threshold: int = 30) -> int:
        return self.storage.cleanup_old_conversations(days_threshold)
