# src/chat_history/storage/json_storage.py
import json
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from .base_storage import BaseConversationStorage
from ..models import Conversation, ConversationSummary


class JsonConversationStorage(BaseConversationStorage):

    def __init__(self, storage_dir: str = "chat_history"):
        self.storage_dir = Path(storage_dir)
        self.conversations_dir = self.storage_dir / "conversations"
        self.index_file = self.storage_dir / "index.json"

        self._ensure_directories()
        self._load_index()

    def _ensure_directories(self) -> None:
        self.storage_dir.mkdir(exist_ok=True)
        self.conversations_dir.mkdir(exist_ok=True)

    def _load_index(self) -> None:
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    self.index = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                self.index = {}
        else:
            self.index = {}

    def _save_index(self) -> None:
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(self.index, f, indent=2, ensure_ascii=False)

    def _get_conversation_file(self, session_id: str) -> Path:
        return self.conversations_dir / f"{session_id}.json"

    def _update_index(self, conversation: Conversation) -> None:
        summary = ConversationSummary.from_conversation(conversation)
        self.index[conversation.session_id] = {
            "title": summary.title,
            "message_count": summary.message_count,
            "last_activity": summary.last_activity.isoformat(),
            "document_name": summary.document_name,
            "agent_type": summary.agent_type,
            "tags": summary.tags,
            "created_at": conversation.created_at.isoformat(),
            "is_active": conversation.is_active
        }
        self._save_index()

    def save_conversation(self, conversation: Conversation) -> None:
        conversation_file = self._get_conversation_file(conversation.session_id)

        with open(conversation_file, 'w', encoding='utf-8') as f:
            json.dump(conversation.to_dict(), f, indent=2, ensure_ascii=False)

        self._update_index(conversation)

    def load_conversation(self, session_id: str) -> Optional[Conversation]:
        conversation_file = self._get_conversation_file(session_id)

        if not conversation_file.exists():
            return None

        try:
            with open(conversation_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return Conversation.from_dict(data)
        except (json.JSONDecodeError, KeyError, ValueError):
            return None

    def delete_conversation(self, session_id: str) -> bool:
        conversation_file = self._get_conversation_file(session_id)

        if conversation_file.exists():
            conversation_file.unlink()

        if session_id in self.index:
            del self.index[session_id]
            self._save_index()
            return True

        return False

    def list_conversations(self, limit: Optional[int] = None,
                          offset: int = 0) -> List[ConversationSummary]:
        sorted_conversations = sorted(
            self.index.items(),
            key=lambda x: datetime.fromisoformat(x[1]["last_activity"]),
            reverse=True
        )

        if offset > 0:
            sorted_conversations = sorted_conversations[offset:]

        if limit:
            sorted_conversations = sorted_conversations[:limit]

        summaries = []
        for session_id, data in sorted_conversations:
            summary = ConversationSummary(
                session_id=session_id,
                title=data["title"],
                message_count=data["message_count"],
                last_activity=datetime.fromisoformat(data["last_activity"]),
                document_name=data.get("document_name"),
                agent_type=data.get("agent_type"),
                tags=data.get("tags", [])
            )
            summaries.append(summary)

        return summaries

    def search_conversations(self, query: str, limit: Optional[int] = None) -> List[ConversationSummary]:
        query_lower = query.lower()
        matching_summaries = []

        for session_id, data in self.index.items():
            if (query_lower in data["title"].lower() or
                any(query_lower in tag.lower() for tag in data.get("tags", [])) or
                (data.get("document_name") and query_lower in data["document_name"].lower())):

                summary = ConversationSummary(
                    session_id=session_id,
                    title=data["title"],
                    message_count=data["message_count"],
                    last_activity=datetime.fromisoformat(data["last_activity"]),
                    document_name=data.get("document_name"),
                    agent_type=data.get("agent_type"),
                    tags=data.get("tags", [])
                )
                matching_summaries.append(summary)

        matching_summaries.sort(key=lambda x: x.last_activity, reverse=True)

        if limit:
            matching_summaries = matching_summaries[:limit]

        return matching_summaries

    def get_conversations_by_document(self, document_name: str) -> List[ConversationSummary]:
        return [
            ConversationSummary(
                session_id=session_id,
                title=data["title"],
                message_count=data["message_count"],
                last_activity=datetime.fromisoformat(data["last_activity"]),
                document_name=data.get("document_name"),
                agent_type=data.get("agent_type"),
                tags=data.get("tags", [])
            )
            for session_id, data in self.index.items()
            if data.get("document_name") == document_name
        ]

    def get_conversations_by_agent(self, agent_type: str) -> List[ConversationSummary]:
        return [
            ConversationSummary(
                session_id=session_id,
                title=data["title"],
                message_count=data["message_count"],
                last_activity=datetime.fromisoformat(data["last_activity"]),
                document_name=data.get("document_name"),
                agent_type=data.get("agent_type"),
                tags=data.get("tags", [])
            )
            for session_id, data in self.index.items()
            if data.get("agent_type") == agent_type
        ]

    def get_conversation_count(self) -> int:
        return len(self.index)

    def cleanup_old_conversations(self, days_threshold: int = 30) -> int:
        cutoff_date = datetime.now() - timedelta(days=days_threshold)
        deleted_count = 0

        sessions_to_delete = []
        for session_id, data in self.index.items():
            last_activity = datetime.fromisoformat(data["last_activity"])
            if last_activity < cutoff_date:
                sessions_to_delete.append(session_id)

        for session_id in sessions_to_delete:
            if self.delete_conversation(session_id):
                deleted_count += 1

        return deleted_count

    def export_conversation(self, session_id: str, format: str = "json") -> Optional[Dict[str, Any]]:
        conversation = self.load_conversation(session_id)
        if not conversation:
            return None

        if format == "json":
            return conversation.to_dict()

        return None

    def import_conversation(self, conversation_data: Dict[str, Any]) -> bool:
        try:
            conversation = Conversation.from_dict(conversation_data)
            self.save_conversation(conversation)
            return True
        except (KeyError, ValueError, TypeError):
            return False
